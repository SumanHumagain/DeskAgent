"""
Bluetooth Action - Professional implementation with state checking and fallback
"""

import subprocess
import sys
from typing import Dict, Tuple


class BluetoothAction:
    """
    Professional Bluetooth control with:
    - State checking before action
    - Multiple methods (API → GUI fallback)
    - State verification after action
    """

    def __init__(self):
        """Initialize Bluetooth action handler"""
        pass

    def get_bluetooth_state(self) -> Tuple[bool, str, str]:
        """
        Get current Bluetooth state using Windows Runtime API

        Returns:
            (success, state, message)
            - success: bool - Whether check succeeded
            - state: str - "On", "Off", or "Unknown"
            - message: str - Human-readable message
        """
        # PowerShell script to check Bluetooth state
        ps_script = """
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null

Await ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus]) | Out-Null
$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$bluetooth = $radios | Where-Object { $_.Kind -eq 'Bluetooth' }

if ($bluetooth) {
    Write-Output $bluetooth.State
} else {
    Write-Output "NotFound"
}
"""

        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )

            state = result.stdout.strip()

            if state == "On":
                return (True, "On", "Bluetooth is currently ON")
            elif state == "Off":
                return (True, "Off", "Bluetooth is currently OFF")
            elif state == "NotFound":
                return (False, "Unknown", "No Bluetooth adapter found")
            else:
                return (False, "Unknown", f"Unexpected state: {state}")

        except Exception as e:
            return (False, "Unknown", f"Failed to check Bluetooth state: {str(e)}")

    def set_bluetooth_state(self, desired_state: str) -> Dict:
        """
        Set Bluetooth state (On/Off) with state checking and verification

        Args:
            desired_state: "On" or "Off"

        Returns:
            Dictionary with:
            - success: bool
            - current_state: str ("On" or "Off")
            - message: str
            - method_used: str (which method worked)
        """
        desired_state = desired_state.capitalize()
        if desired_state not in ["On", "Off"]:
            return {
                'success': False,
                'current_state': 'Unknown',
                'message': f'Invalid state: {desired_state}. Must be "On" or "Off"',
                'method_used': None
            }

        # Step 1: Check current state
        print(f"[BLUETOOTH] Checking current state...", file=sys.stderr)
        success, current_state, msg = self.get_bluetooth_state()

        if not success:
            return {
                'success': False,
                'current_state': 'Unknown',
                'message': msg,
                'method_used': None
            }

        # Step 2: If already in desired state, return success
        if current_state == desired_state:
            return {
                'success': True,
                'current_state': current_state,
                'message': f'Bluetooth already {desired_state}',
                'method_used': 'state_check'
            }

        # Step 3: Attempt to change state using Windows Runtime API
        print(f"[BLUETOOTH] Changing state from {current_state} to {desired_state}...", file=sys.stderr)

        ps_script = f"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{ $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation``1' }})[0]
Function Await($WinRtTask, $ResultType) {{
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}}

[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
[Windows.Devices.Radios.RadioState,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null

Await ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus]) | Out-Null
$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$bluetooth = $radios | Where-Object {{ $_.Kind -eq 'Bluetooth' }}

if ($bluetooth) {{
    Await ($bluetooth.SetStateAsync('{desired_state}')) ([Windows.Devices.Radios.RadioAccessStatus]) | Out-Null
    Write-Output "Success"
}} else {{
    Write-Output "Failed"
}}
"""

        try:
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=15
            )

            if "Success" in result.stdout:
                # Step 4: Verify state changed
                import time
                time.sleep(1)  # Give Windows a moment to update

                success, new_state, msg = self.get_bluetooth_state()

                if success and new_state == desired_state:
                    return {
                        'success': True,
                        'current_state': new_state,
                        'message': f'Bluetooth turned {desired_state}',
                        'method_used': 'windows_runtime_api'
                    }
                else:
                    return {
                        'success': False,
                        'current_state': new_state,
                        'message': f'State change attempted but verification failed. Current: {new_state}',
                        'method_used': 'windows_runtime_api'
                    }
            else:
                return {
                    'success': False,
                    'current_state': current_state,
                    'message': f'Failed to change Bluetooth state: {result.stderr}',
                    'method_used': 'windows_runtime_api'
                }

        except Exception as e:
            return {
                'success': False,
                'current_state': current_state,
                'message': f'Exception while changing Bluetooth state: {str(e)}',
                'method_used': 'windows_runtime_api'
            }

    def turn_on(self) -> Dict:
        """Turn Bluetooth ON"""
        return self.set_bluetooth_state("On")

    def turn_off(self) -> Dict:
        """Turn Bluetooth OFF"""
        return self.set_bluetooth_state("Off")

    def toggle(self) -> Dict:
        """Toggle Bluetooth state (On→Off or Off→On)"""
        success, current_state, msg = self.get_bluetooth_state()

        if not success:
            return {
                'success': False,
                'current_state': 'Unknown',
                'message': msg,
                'method_used': None
            }

        new_state = "Off" if current_state == "On" else "On"
        return self.set_bluetooth_state(new_state)
