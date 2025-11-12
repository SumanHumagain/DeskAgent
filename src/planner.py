"""
LLM Planner - Converts natural language prompts to structured action plans
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
from openai import OpenAI


class Planner:
    """Converts user prompts into structured action plans using LLM"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('MODEL_NAME', 'gpt-4o-mini')
        self.action_schema = self._load_action_schema()
        self.recent_messages_count = 5  # Keep last 5 messages in full

    def _load_action_schema(self) -> dict:
        """Load the action schema from config"""
        schema_path = Path(__file__).parent.parent / 'config' / 'action_schema.json'

        if not schema_path.exists():
            raise FileNotFoundError(f"Action schema not found at {schema_path}")

        with open(schema_path, 'r') as f:
            return json.load(f)

    def _summarize_old_history(self, old_messages: List[Dict]) -> str:
        """
        Summarize older conversation history to save tokens

        Args:
            old_messages: List of older messages to summarize

        Returns:
            Summary string
        """
        if not old_messages:
            return ""

        # Build a compact summary
        summary_parts = []
        user_queries = []

        for msg in old_messages:
            msg_type = msg.get('type', '')
            content = msg.get('content', '')

            if msg_type == 'user':
                # Keep user queries (most important for context)
                user_queries.append(content[:100])  # Truncate to 100 chars
            elif msg_type == 'success':
                # Just note that it succeeded
                summary_parts.append(f"Executed successfully")

        summary = "Previous conversation summary:\n"
        if user_queries:
            summary += f"User asked: {' | '.join(user_queries[-3:])}\n"  # Last 3 queries

        return summary

    def _build_system_prompt(self) -> str:
        """Build the system prompt with action schema"""
        actions_desc = []

        for action in self.action_schema['actions']:
            args_desc = []
            for arg_name, arg_spec in action['args'].items():
                required = arg_spec.get('required', False)
                req_str = 'REQUIRED' if required else 'optional'
                args_desc.append(f"  - {arg_name} ({arg_spec['type']}, {req_str}): {arg_spec['description']}")

            action_desc = f"""
Action: {action['action']}
Description: {action['description']}
Risk Level: {action['risk_level']}
Arguments:
{chr(10).join(args_desc)}

Example:
{json.dumps(action['example'], indent=2)}
"""
            actions_desc.append(action_desc)

        system_prompt = f"""You are an intelligent Desktop Automation Assistant for Windows.

Your task: Determine if the user wants to chat OR perform actions, then respond appropriately.

**IF the user is chatting** (greetings, questions, casual conversation, or asking about conversation history):
- Return a CHAT response: {{"action": "chat", "args": {{"message": "Your friendly response here"}}}}
- Examples: "hi", "hello", "how are you", "what can you do?", "thanks"
- **CONVERSATION HISTORY QUESTIONS**: You HAVE ACCESS to conversation history! Answer questions like:
  * "what was my last query?" → Check recent user messages in conversation history
  * "did I ask to increase speaker?" → Search conversation history for speaker/volume requests
  * "what was my 6th query?" → Count user messages and retrieve the 6th one
  * "what did I ask before?" → Summarize previous user requests from history

**IF the user is MODIFYING/REFINING their request** (asking for same data with different formatting):
- Detect exclusion requests: "without pid", "hide pid", "don't show pid", "no memory percent", etc.
- Use the exclude_fields parameter to honor their request
- Examples:
  * "show top processes without pid" → {{"action": "get_top_processes_by_memory", "args": {{"limit": 5, "exclude_fields": ["pid"]}}}}
  * "give result without pid" (after a process list request) → {{"action": "get_top_processes_by_memory", "args": {{"limit": 5, "exclude_fields": ["pid"]}}}}
  * "hide memory percent" → add "memory_percent" to exclude_fields
  * "just show names and RAM" → include exclude_fields with pid and memory_percent

**IF the user is giving GENERAL FEEDBACK** (not asking for re-execution):
- Return a CHAT response acknowledging the feedback
- Examples: "that's too much info" (without asking to re-run), "I don't need that detail", "show less info"
- Only use CHAT if they're NOT asking for the same data again

**IF the user wants actions** (file operations, automation tasks):
- Convert to a JSON array of structured actions that can be executed sequentially

STRICT RULES:
1. ONLY output valid JSON - no explanations, no markdown, no extra text
2. ONLY use actions from the allowed list below OR use "chat" action
3. Each action must have "action" and "args" fields
4. Validate that required arguments are present
5. Use Windows path format (C:\\Users\\...)
6. Use %USERNAME% for user directories - it will be auto-expanded

ADVANCED FEATURES:
7. **Action Chaining**: You can reference outputs from previous actions using {{{{RESULT_X}}}} syntax where X is the action index (0-based)
   - Example: {{{{"RESULT_0.files[0].path"}}}} gets the first file path from action 0
   - Example: {{{{"RESULT_0.files[0].name"}}}} gets the file name
   - This allows multi-step workflows like "find a file, then copy it"

8. **Smart Planning**: Break down complex requests into logical steps:
   - User: "find latest PDF and copy to S drive" →
     [
       {{"action": "find_file", "args": {{"path": "C:\\\\Users\\\\%USERNAME%\\\\Downloads", "pattern": "*.pdf", "latest": true, "show_in_explorer": false}}}},
       {{"action": "copy_file", "args": {{"source": "{{{{"RESULT_0.files[0].path"}}}}", "destination": "S:\\\\"}}}}
     ]

9. **Smart File Search - IMPORTANT**: When searching for files:
   - AVOID searching entire C:\\ drive (extremely slow!)
   - Default to common user folders: Downloads, Documents, Desktop
   - User: "find X on my computer" → search "C:\\\\Users\\\\%USERNAME%\\\\Downloads" NOT "C:\\\\"
   - Only search C:\\ if explicitly asked "search entire computer" or "search C drive"
   - Example: "find password file" → search Downloads/Documents/Desktop, NOT C:\\
   - **For folder-based searches**: User asks "find file in lab 5 folder" → Don't assume exact path!
     Use recursive search: {{"action": "find_file", "args": {{"path": "C:\\\\Users\\\\%USERNAME%\\\\Documents", "pattern": "*lab*5*.docx", "recursive": true}}}}
     This searches for files matching the pattern anywhere under Documents

10. **Windows Application Launching - USE YOUR KNOWLEDGE**: Intelligently map user requests to correct Windows commands:
   - "control panel" → {{"action": "launch_app", "args": {{"command": "control"}}}}
   - "task manager" → {{"action": "launch_app", "args": {{"command": "taskmgr"}}}}
   - "device manager" → {{"action": "launch_app", "args": {{"command": "devmgmt.msc"}}}}
   - "settings" → {{"action": "launch_app", "args": {{"command": "ms-settings:"}}}}
   - "notepad" → {{"action": "launch_app", "args": {{"command": "notepad.exe"}}}}
   - "calculator" → {{"action": "launch_app", "args": {{"command": "calc.exe"}}}}

   **Microsoft Office apps - IMPORTANT**: Use 'start' command:
   - "excel" / "open excel" → {{"action": "launch_app", "args": {{"command": "start excel"}}}}
   - "word" / "open word" → {{"action": "launch_app", "args": {{"command": "start winword"}}}}
   - "powerpoint" → {{"action": "launch_app", "args": {{"command": "start powerpnt"}}}}
   - "outlook" → {{"action": "launch_app", "args": {{"command": "start outlook"}}}}

   Use your Windows knowledge to determine the correct command for ANY system utility or app

11. **GUI Navigation for Complex Tasks - VERY IMPORTANT**: Use your Windows knowledge to navigate ANY Windows UI:

   **How navigate_settings works:**
   - ui_path: Array of UI elements to click through (e.g., window names, button names, tab names)
   - action: The final action to perform (checkbox, slider, button, etc.)

   **Common Windows UI Patterns (use your knowledge):**
   - Control Panel items: "Control Panel" → "Mouse" → "Pointer Options" tab → slider/checkbox
   - System Tray icons: Click icon name (e.g., "Speakers", "Network", "Battery") to open popup → interact with controls
   - Settings app: "Settings" → category → subcategory → control
   - Right-click menus: Specify "Right-click" in path

   **Examples:**
   - "show hidden files" → You know this is in Control Panel > File Explorer Options > View tab > checkbox
     {{"action": "navigate_settings", "args": {{"ui_path": ["Control Panel", "File Explorer Options", "View"], "action": {{"type": "checkbox", "name": "Show hidden files", "value": true}}}}}}

   - "change mouse speed to slowest" → You know this is in Control Panel > Mouse > Pointer Options tab > speed slider
     {{"action": "navigate_settings", "args": {{"ui_path": ["Control Panel", "Mouse", "Pointer Options"], "action": {{"type": "slider", "name": "speed", "value": "slow"}}}}}}

   - "mute speaker" / "unmute speaker" / "set volume" → The system has DYNAMIC volume control with auto-fallback
     Simply use: {{"action": "navigate_settings", "args": {{"ui_path": ["Volume"], "action": {{"type": "slider", "name": "volume", "value": "min|max|mid"}}}}}}
     The system will automatically try: system tray → quick settings → PowerShell → settings app

   - "increase volume" / "volume max" / "unmute" →
     {{"action": "navigate_settings", "args": {{"ui_path": ["Volume"], "action": {{"type": "slider", "name": "volume", "value": "max"}}}}}}

   - "turn on bluetooth" → Use ai_navigate action (AI will analyze UI and figure out what to do dynamically):
     {{"action": "ai_navigate", "args": {{"goal": "turn on bluetooth", "window_search_terms": ["Settings", "Bluetooth"], "open_command": "start ms-settings:bluetooth"}}}}

   **Key principle - TRULY DYNAMIC APPROACH:**

   **For QUERIES (check, show, what is, tell me):**
   - Use "run_python_code" action - Generate Python code dynamically!
   - Examples:
     * "check battery" → Generate: `import psutil; battery = psutil.sensors_battery(); result = {{'percentage': battery.percent, 'status': 'Charging' if battery.power_plugged else 'Discharging'}}; print(result)`
     * "show CPU usage" → Generate: `import psutil; print(f"CPU: {{psutil.cpu_percent()}}%")`
     * "disk space on C drive" → Generate: `import psutil; disk = psutil.disk_usage('C:\\\\'); print(f"Free: {{disk.free/1024**3:.1f}}GB")`
     * "list running processes" → Generate: `import psutil; [print(p.name()) for p in psutil.process_iter()]`
   - YOU generate the code based on what user wants - infinite flexibility!
   - Available modules: psutil, os, sys, pathlib, json, datetime, etc.

   **For SYSTEM OPERATIONS (uninstall, install, configure, manage):**
   - Use "run_powershell" action - Generate PowerShell script dynamically!
   - Examples:
     * "uninstall adobe software" → Generate: `Get-WmiObject -Class Win32_Product | Where-Object {{$_.Name -like '*Adobe*'}} | ForEach-Object {{ Write-Host "Uninstalling: $($_.Name)"; $_.Uninstall() }}`
     * "list installed programs" → Generate: `Get-WmiObject -Class Win32_Product | Select-Object Name, Version | Sort-Object Name`
     * "stop a service" → Generate: `Stop-Service -Name "ServiceName" -Force`
     * "clear temp files" → Generate: `Remove-Item -Path "$env:TEMP\\*" -Recurse -Force`
   - YOU generate the PowerShell based on what user wants!
   - Use WMI, registry, services, file operations, etc.

   **For ACTIONS (turn on/off, change, adjust):**
   - Use "ai_navigate" action - AI will analyze UI in real-time
   - The AI will figure out what controls exist and how to interact
   - This works for ANY setting, even if it changes between Windows versions

   **IMPORTANT - Windows Security / Defender:**
   - For virus scans, threat protection, etc., use: "windowsdefender:" protocol (NOT ms-settings)
   - Example: "windowsdefender:" opens Windows Security app directly
   - The window will be titled "Windows Security" - use that in window_search_terms
   - Common paths:
     * Virus scan: windowsdefender: → Windows Security → Virus & threat protection → Quick scan
     * Firewall: Use "ms-settings:windowsdefender-firewall" → Settings → Network & internet

   **SPECIAL CASES - Use direct API control for more reliability:**
   - Brightness: Use "run_powershell" with WMI to directly control brightness
     * "increase brightness" → `$brightness = (Get-Ciminstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness; $newBrightness = [Math]::Min(100, $brightness + 10); (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,$newBrightness)`
     * "decrease brightness" → `$brightness = (Get-Ciminstance -Namespace root/WMI -ClassName WmiMonitorBrightness).CurrentBrightness; $newBrightness = [Math]::Max(0, $brightness - 10); (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,$newBrightness)`
     * "set brightness to 50%" → `(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,50)`
   - This directly controls brightness via Windows API - much more reliable than GUI!

ALLOWED ACTIONS:
{chr(10).join(actions_desc)}

OUTPUT FORMAT:
Return a JSON array like this:
{json.dumps(self.action_schema['output_format_example'], indent=2)}

**For complex multi-step tasks**, chain actions together:
[
  {{"action": "find_file", ...}},
  {{"action": "copy_file", "args": {{"source": "{{{{"RESULT_0.files[0].path"}}}}", ...}}}}
]

Remember:
- Think intelligently about what the user wants
- Break complex tasks into simple steps
- Use action chaining for dependent steps
- ONLY JSON output, nothing else!
"""
        return system_prompt

    def create_plan(self, user_prompt: str, conversation_history: Optional[List[Dict]] = None) -> Optional[List[Dict]]:
        """
        Convert user prompt to structured action plan

        Args:
            user_prompt: Natural language request from user
            conversation_history: Previous messages for context (optional)

        Returns:
            List of action dictionaries, or None if planning failed
        """
        try:
            # Build messages starting with system prompt
            messages = [
                {"role": "system", "content": self._build_system_prompt()}
            ]

            # Add conversation history with smart summarization
            if conversation_history and len(conversation_history) > 0:
                # Split into old (to summarize) and recent (keep in full)
                if len(conversation_history) > self.recent_messages_count:
                    old_messages = conversation_history[:-self.recent_messages_count]
                    recent_messages = conversation_history[-self.recent_messages_count:]

                    # Add summarized old history
                    summary = self._summarize_old_history(old_messages)
                    if summary:
                        messages.append({"role": "system", "content": summary})
                else:
                    recent_messages = conversation_history

                # Add recent messages in full
                for msg in recent_messages:
                    msg_type = msg.get('type', '')
                    msg_content = msg.get('content', '')

                    # Map message types to OpenAI roles
                    if msg_type == 'user':
                        messages.append({"role": "user", "content": msg_content})
                    elif msg_type in ['success', 'plan', 'warning', 'error']:
                        # These are all assistant responses (plans, results, errors)
                        # Truncate long outputs to save tokens
                        content_preview = msg_content[:500] if len(msg_content) > 500 else msg_content
                        if msg_type == 'plan':
                            messages.append({"role": "assistant", "content": f"Plan: {content_preview}"})
                        elif msg_type == 'success':
                            messages.append({"role": "assistant", "content": f"Result: {content_preview}"})
                        elif msg_type == 'warning':
                            messages.append({"role": "assistant", "content": f"Warning: {content_preview}"})
                        elif msg_type == 'error':
                            messages.append({"role": "assistant", "content": f"Error: {content_preview}"})

            # Add current user prompt
            messages.append({"role": "user", "content": user_prompt})

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,  # Low temperature for more deterministic output
                max_tokens=1000
            )

            # Extract and parse response
            response_text = response.choices[0].message.content.strip()

            # Handle markdown code blocks (sometimes LLM wraps in ```)
            if response_text.startswith('```'):
                # Remove markdown code block formatting
                response_text = response_text.strip('`').strip()
                if response_text.startswith('json'):
                    response_text = response_text[4:].strip()

            # Parse JSON
            plan = json.loads(response_text)

            # If LLM returned a single dict instead of list, wrap it
            if isinstance(plan, dict):
                plan = [plan]

            # Validate it's a list
            if not isinstance(plan, list):
                print(f"Error: LLM returned invalid type: {type(plan)}", file=sys.stderr)
                return None

            # Check for clarification request
            if len(plan) == 1 and plan[0].get('action') == 'clarify':
                question = plan[0].get('args', {}).get('question', 'Unknown question')
                print(f"\nClarification needed: {question}", file=sys.stderr)
                return None

            # Add risk levels from schema
            plan = self._enrich_plan_with_metadata(plan)

            return plan

        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse LLM response as JSON: {e}", file=sys.stderr)
            print(f"Response was: {response_text[:200]}...", file=sys.stderr)
            return None

        except Exception as e:
            print(f"Error creating plan: {e}", file=sys.stderr)
            return None

    def _enrich_plan_with_metadata(self, plan: List[Dict]) -> List[Dict]:
        """Add metadata like risk_level to each action"""
        schema_map = {
            action['action']: action
            for action in self.action_schema['actions']
        }

        enriched_plan = []
        for step in plan:
            action_name = step.get('action')
            if action_name in schema_map:
                step['risk_level'] = schema_map[action_name]['risk_level']
                step['description'] = schema_map[action_name]['description']

            enriched_plan.append(step)

        return enriched_plan
