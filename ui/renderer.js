// UI Elements
const promptInput = document.getElementById('promptInput');
const sendBtn = document.getElementById('sendBtn');
const stopBtn = document.getElementById('stopBtn');
const helpBtn = document.getElementById('helpBtn');
const logsBtn = document.getElementById('logsBtn');
const clearBtn = document.getElementById('clearBtn');
const outputArea = document.getElementById('outputArea');
const historyList = document.getElementById('historyList');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const newChatBtn = document.getElementById('newChatBtn');

let currentPlan = null;
let isProcessing = false;
let shouldStop = false;
let lastResult = null; // Store last result for client-side reformatting

// Conversation management
let conversations = [];
let currentConversationId = null;

// Generate unique ID
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// Load conversations from localStorage
function loadConversations() {
    const saved = localStorage.getItem('conversations');
    if (saved) {
        conversations = JSON.parse(saved);
    }

    // Create initial conversation if none exists
    if (conversations.length === 0) {
        createNewConversation();
    } else {
        // Load the most recent conversation
        currentConversationId = conversations[0].id;
        loadConversation(currentConversationId);
    }

    renderConversationList();
}

// Save conversations to localStorage
function saveConversations() {
    localStorage.setItem('conversations', JSON.stringify(conversations));
}

// Create new conversation
function createNewConversation() {
    const newConversation = {
        id: generateId(),
        title: 'New Chat',
        timestamp: new Date().toISOString(),
        messages: []
    };

    conversations.unshift(newConversation);
    currentConversationId = newConversation.id;

    // Clear output area
    outputArea.innerHTML = '';

    saveConversations();
    renderConversationList();
}

// Load conversation by ID
function loadConversation(conversationId) {
    const conversation = conversations.find(c => c.id === conversationId);
    if (!conversation) return;

    currentConversationId = conversationId;

    // Clear and reload messages
    outputArea.innerHTML = '';
    conversation.messages.forEach(msg => {
        addMessageToDOM(msg.type, msg.title, msg.content, msg.data);
    });

    renderConversationList();
}

// Delete conversation
function deleteConversation(conversationId, event) {
    if (event) {
        event.stopPropagation();
    }

    const index = conversations.findIndex(c => c.id === conversationId);
    if (index === -1) return;

    conversations.splice(index, 1);

    // If we deleted the current conversation, create a new one
    if (conversationId === currentConversationId) {
        if (conversations.length > 0) {
            loadConversation(conversations[0].id);
        } else {
            createNewConversation();
        }
    }

    saveConversations();
    renderConversationList();
}

// Render conversation list in sidebar
function renderConversationList() {
    historyList.innerHTML = '';

    conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = 'history-item';
        if (conv.id === currentConversationId) {
            item.classList.add('active');
        }

        const content = document.createElement('div');
        content.className = 'history-item-content';

        const title = document.createElement('div');
        title.className = 'history-item-title';
        title.textContent = conv.title;

        const time = document.createElement('div');
        time.className = 'history-item-time';
        const date = new Date(conv.timestamp);
        const now = new Date();
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            time.textContent = 'Today';
        } else if (diffDays === 1) {
            time.textContent = 'Yesterday';
        } else if (diffDays < 7) {
            time.textContent = `${diffDays} days ago`;
        } else {
            time.textContent = date.toLocaleDateString();
        }

        content.appendChild(title);
        content.appendChild(time);

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-chat-btn';
        deleteBtn.innerHTML = '×';
        deleteBtn.title = 'Delete chat';
        deleteBtn.addEventListener('click', (e) => deleteConversation(conv.id, e));

        item.appendChild(content);
        item.appendChild(deleteBtn);

        item.addEventListener('click', () => {
            if (conv.id !== currentConversationId) {
                loadConversation(conv.id);
            }
        });

        historyList.appendChild(item);
    });
}

// Update conversation title based on first message
function updateConversationTitle(conversationId, firstMessage) {
    const conversation = conversations.find(c => c.id === conversationId);
    if (!conversation) return;

    // Only update if still has default title
    if (conversation.title === 'New Chat') {
        conversation.title = firstMessage.substring(0, 40) + (firstMessage.length > 40 ? '...' : '');
        saveConversations();
        renderConversationList();
    }
}

// Save message to current conversation
function saveMessageToConversation(type, title, content, data = null) {
    const conversation = conversations.find(c => c.id === currentConversationId);
    if (!conversation) return;

    conversation.messages.push({ type, title, content, data });
    conversation.timestamp = new Date().toISOString();

    // Update title if this is a user message and conversation is still "New Chat"
    if (type === 'user' && conversation.title === 'New Chat') {
        updateConversationTitle(currentConversationId, content);
    }

    saveConversations();
}

// Clear all conversations
clearHistoryBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to delete all chat history?')) {
        conversations = [];
        createNewConversation();
    }
});

// New chat button
newChatBtn.addEventListener('click', () => {
    createNewConversation();
});

// Initialize
loadConversations();

// Add message to DOM only (for loading saved conversations)
function addMessageToDOM(type, title, content, data = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    let html = `<strong>${title}</strong><div class="message-content">${content}</div>`;

    if (data && data.plan) {
        html += '<div class="action-plan">';
        html += '<div style="font-weight: bold; margin-bottom: 10px;">Planned Actions:</div>';
        data.plan.forEach((action, index) => {
            const riskColor = action.risk_level === 'low' ? '#4CAF50' :
                            action.risk_level === 'high' ? '#f44336' : '#ff9800';
            html += `<div class="action-item" style="border-left-color: ${riskColor}">`;
            html += `<div class="action-name">${index + 1}. ${action.action}</div>`;
            if (action.args) {
                html += '<div class="action-args">';
                for (const [key, value] of Object.entries(action.args)) {
                    html += `${key}: ${value}<br>`;
                }
                html += '</div>';
            }
            html += '</div>';
        });
        html += '</div>';
    }

    if (data && data.results) {
        html += '<div class="action-plan">';
        html += '<div style="font-weight: bold; margin-bottom: 10px;">Execution Results:</div>';
        data.results.forEach((result, index) => {
            const statusColor = result.status === 'success' ? '#4CAF50' : '#f44336';
            html += `<div class="action-item" style="border-left-color: ${statusColor}">`;
            html += `<div class="action-name">${index + 1}. ${result.action}</div>`;
            html += `<div class="action-args">Status: ${result.status}</div>`;
            if (result.error) {
                html += `<div class="action-args" style="color: #f44336;">Error: ${result.error}</div>`;
            }
            html += '</div>';
        });
        html += '</div>';
    }

    messageDiv.innerHTML = html;
    outputArea.appendChild(messageDiv);
    outputArea.scrollTop = outputArea.scrollHeight;
}

// Detect if user is asking to reformat the last result (not re-execute)
function isFormattingOnlyRequest(prompt) {
    const formattingPatterns = [
        /^(give|show)\s+(result|output|that)\s+(without|hide|no|remove)\s+(\w+)$/i,
        /^without\s+(\w+)$/i,
        /^hide\s+(\w+)$/i,
        /^(don't|do not)\s+show\s+(\w+)$/i,
        /^remove\s+(\w+)$/i
    ];

    return formattingPatterns.some(pattern => pattern.test(prompt.trim()));
}

// Extract fields to exclude from user request
function extractExcludeFields(prompt) {
    const excludeFields = [];
    const lowerPrompt = prompt.toLowerCase();

    if (lowerPrompt.includes('without pid') || lowerPrompt.includes('hide pid') || lowerPrompt.includes('no pid')) {
        excludeFields.push('pid');
    }
    if (lowerPrompt.includes('without memory percent') || lowerPrompt.includes('hide memory percent')) {
        excludeFields.push('memory_percent');
    }
    if (lowerPrompt.includes('without memory') || lowerPrompt.includes('hide memory')) {
        excludeFields.push('memory_mb');
    }

    return excludeFields;
}

// Reformat last result with exclusions
function reformatLastResult(excludeFields) {
    if (!lastResult || !lastResult.output) {
        return null;
    }

    // Clone the output to avoid modifying original
    const reformattedOutput = JSON.parse(JSON.stringify(lastResult.output));

    // Apply exclusions to process list
    if (reformattedOutput.top_processes && Array.isArray(reformattedOutput.top_processes)) {
        reformattedOutput.top_processes.forEach(proc => {
            excludeFields.forEach(field => {
                delete proc[field];
            });
        });
        reformattedOutput.exclude_fields = excludeFields;
    }

    return reformattedOutput;
}

// Format system information output for readability
function formatSystemInfo(output, description) {
    if (!output || typeof output !== 'object') {
        // Check if it's a multi-step wizard output
        if (typeof output === 'string' && output.includes('steps:')) {
            // Format wizard steps nicely
            return output.replace(/Clicked/g, '✓ Clicked');
        }
        return String(output);
    }

    let formatted = '';

    // Battery info
    if (output.percentage !== undefined) {
        formatted += `🔋 Battery: ${output.percentage}%`;
        if (output.status) {
            formatted += ` (${output.status})`;
        }
        if (output.time_remaining) {
            formatted += `\nTime remaining: ${output.time_remaining}`;
        }
        return formatted;
    }

    // RAM info
    if (output.total !== undefined && output.percent !== undefined) {
        const totalGB = (output.total / (1024**3)).toFixed(1);
        const usedGB = (output.used / (1024**3)).toFixed(1);
        const availableGB = (output.available / (1024**3)).toFixed(1);

        formatted += `💾 RAM: ${output.percent}% used\n`;
        formatted += `   Total: ${totalGB} GB\n`;
        formatted += `   Used: ${usedGB} GB\n`;
        formatted += `   Available: ${availableGB} GB`;
        return formatted;
    }

    // CPU info
    if (output.cpu_percent !== undefined) {
        formatted += `⚡ CPU: ${output.cpu_percent}%`;
        if (output.cpu_count) {
            formatted += ` (${output.cpu_count} cores)`;
        }
        return formatted;
    }

    // Disk info
    if (output.drive !== undefined) {
        const freeGB = output.free_gb || (output.free / (1024**3)).toFixed(1);
        const totalGB = output.total_gb || (output.total / (1024**3)).toFixed(1);

        formatted += `💿 Disk ${output.drive}: ${output.percent_used || output.percent}% used\n`;
        formatted += `   Free: ${freeGB} GB / ${totalGB} GB`;
        return formatted;
    }

    // Top processes by memory - DYNAMIC formatting based on available fields
    if (output.top_processes && Array.isArray(output.top_processes)) {
        formatted += `📊 Top ${output.top_processes.length} Processes by Memory Usage:\n\n`;
        output.top_processes.forEach((proc, index) => {
            formatted += `${index + 1}. ${proc.name}\n`;

            // Build details line dynamically based on what fields are present
            let details = [];

            if (proc.memory_mb !== undefined) {
                const memoryGB = (proc.memory_mb / 1024).toFixed(2);
                details.push(`RAM: ${proc.memory_mb.toFixed(0)} MB (${memoryGB} GB)`);
            }

            if (proc.memory_percent !== undefined) {
                details.push(`${proc.memory_percent.toFixed(1)}%`);
            }

            if (proc.pid !== undefined) {
                details.push(`PID: ${proc.pid}`);
            }

            if (details.length > 0) {
                formatted += `   ${details.join(' - ')}\n\n`;
            } else {
                formatted += '\n';
            }
        });
        return formatted.trim();
    }

    // Default: pretty print JSON
    return JSON.stringify(output, null, 2);
}

// Add message to output and save to conversation
function addMessage(type, title, content, data = null) {
    addMessageToDOM(type, title, content, data);
    saveMessageToConversation(type, title, content, data);
}

// Set processing state
function setProcessing(processing) {
    isProcessing = processing;
    shouldStop = false;
    sendBtn.disabled = processing;

    if (processing) {
        sendBtn.style.display = 'none';
        stopBtn.style.display = 'block';
    } else {
        sendBtn.style.display = 'block';
        stopBtn.style.display = 'none';
    }
}

// Handle stop button
function handleStop() {
    shouldStop = true;
    addMessage('warning', 'Stopped', 'Processing stopped by user.');
    setProcessing(false);
}

// Add thinking indicator
function addThinkingIndicator() {
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'message info thinking-indicator';
    thinkingDiv.innerHTML = `
        <strong>Agent</strong>
        <div class="message-content">
            <span class="loading"></span>
            <span style="margin-left: 8px;">Thinking...</span>
        </div>
    `;
    outputArea.appendChild(thinkingDiv);
    outputArea.scrollTop = outputArea.scrollHeight;
    return thinkingDiv;
}

// Remove thinking indicator
function removeThinkingIndicator(element) {
    if (element && element.parentNode) {
        element.parentNode.removeChild(element);
    }
}

// Handle prompt submission
async function handleSubmit() {
    const prompt = promptInput.value.trim();

    if (!prompt || isProcessing) {
        return;
    }

    // Display user prompt
    addMessage('user', 'You', prompt);
    promptInput.value = '';

    // Check if this is a formatting-only request (client-side optimization)
    if (isFormattingOnlyRequest(prompt) && lastResult) {
        const excludeFields = extractExcludeFields(prompt);

        if (excludeFields.length > 0) {
            // Reformat client-side without backend call
            const reformatted = reformatLastResult(excludeFields);

            if (reformatted) {
                const outputText = formatSystemInfo(reformatted);
                const excludedFieldsList = excludeFields.join(', ');
                addMessage('success', 'Done', `Reformatted (excluding: ${excludedFieldsList})\n\n${outputText}`);
                return;
            }
        }
    }

    setProcessing(true);

    // Add thinking indicator
    const thinkingMsg = addThinkingIndicator();

    try {
        // Get current conversation history
        const conversation = conversations.find(c => c.id === currentConversationId);
        const conversationHistory = conversation ? conversation.messages : [];

        const result = await window.electronAPI.submitPrompt(prompt, conversationHistory);

        // Remove thinking indicator
        removeThinkingIndicator(thinkingMsg);

        if (shouldStop) {
            setProcessing(false);
            return;
        }

        if (result.success) {
            if (result.plan && result.plan.length > 0) {
                currentPlan = result.plan;

                // Check if it's a chat response
                if (result.plan.length === 1 && result.plan[0].action === 'chat') {
                    const message = result.plan[0].args.message || 'Hello!';
                    addMessage('success', 'Agent', message);
                    setProcessing(false);
                    return;
                }

                // Display the plan with detailed steps
                let planDescription = `I will perform ${result.plan.length} action${result.plan.length > 1 ? 's' : ''}:\n\n`;
                result.plan.forEach((action, index) => {
                    planDescription += `${index + 1}. ${action.description || action.action}\n`;
                    if (action.args && Object.keys(action.args).length > 0) {
                        // Show key args
                        const keyArgs = Object.entries(action.args)
                            .filter(([k, v]) => v && k !== 'code' && k !== 'script') // Hide code/script from display
                            .slice(0, 3); // Only show first 3 args
                        if (keyArgs.length > 0) {
                            keyArgs.forEach(([k, v]) => {
                                const displayValue = typeof v === 'string' && v.length > 50
                                    ? v.substring(0, 50) + '...'
                                    : JSON.stringify(v);
                                planDescription += `   • ${k}: ${displayValue}\n`;
                            });
                        }
                    }
                    planDescription += '\n';
                });

                addMessage('plan', 'Plan', planDescription);

                // Auto-execute immediately
                await executeCurrentPlan();
            } else {
                addMessage('error', 'Error', 'Failed to create plan. Try rephrasing.');
                setProcessing(false);
            }
        } else {
            addMessage('error', 'Error', result.error || 'Processing failed.');
            setProcessing(false);
        }
    } catch (error) {
        removeThinkingIndicator(thinkingMsg);
        addMessage('error', 'Error', error.message || 'Backend error.');
        setProcessing(false);
    }
}

// Execute current plan automatically
async function executeCurrentPlan() {
    if (!currentPlan) {
        return;
    }

    // Force UI update
    await new Promise(resolve => setTimeout(resolve, 50));

    try {
        const result = await window.electronAPI.approvePlan(currentPlan);

        if (shouldStop) {
            setProcessing(false);
            return;
        }

        if (result.success) {
            const successCount = result.results.filter(r => r.status === 'success').length;
            const totalCount = result.results.length;

            // Format output from results
            let outputText = '';
            let errorText = '';

            result.results.forEach((r, index) => {
                if (r.status === 'success' && r.output) {
                    // Store last successful result for client-side reformatting
                    if (r.action === 'get_top_processes_by_memory' || r.action === 'run_python_code') {
                        lastResult = r;
                    }

                    // Format the output nicely
                    if (typeof r.output === 'object') {
                        // For objects (like battery/RAM data), format as readable text
                        if (r.action === 'run_python_code' || r.action === 'get_top_processes_by_memory') {
                            outputText += formatSystemInfo(r.output, r.args?.description);
                        } else {
                            outputText += JSON.stringify(r.output, null, 2);
                        }
                    } else {
                        outputText += r.output;
                    }
                    if (index < result.results.length - 1) outputText += '\n\n';
                } else if (r.status === 'error' && r.error) {
                    // Collect error messages
                    errorText += `❌ ${r.action}: ${r.error}\n`;
                }
            });

            if (successCount === totalCount) {
                addMessage('success', 'Done', outputText || `All ${totalCount} action(s) completed successfully!`);
            } else {
                // Show errors prominently
                let failureMessage = `Completed ${successCount}/${totalCount} actions (${totalCount - successCount} failed)\n\n`;
                if (errorText) {
                    failureMessage += `Errors:\n${errorText}\n`;
                }
                if (outputText) {
                    failureMessage += `\nSuccessful outputs:\n${outputText}`;
                }
                addMessage('warning', 'Done', failureMessage);
            }
        } else {
            addMessage('error', 'Failed', result.error || 'Execution error.');
        }
    } catch (error) {
        addMessage('error', 'Error', error.message || 'Execution failed.');
    } finally {
        currentPlan = null;
        setProcessing(false);
    }
}

// Approve plan execution (kept for compatibility but not used in auto-mode)
window.approvePlan = async function() {
    if (!currentPlan || isProcessing) {
        return;
    }

    setProcessing(true);
    addMessage('info', 'Executing', 'Running...');

    try {
        const result = await window.electronAPI.approvePlan(currentPlan);

        if (result.success) {
            const successCount = result.results.filter(r => r.status === 'success').length;
            const totalCount = result.results.length;

            // Format output from results
            let outputText = '';
            let errorText = '';

            result.results.forEach((r, index) => {
                if (r.status === 'success' && r.output) {
                    // Store last successful result for client-side reformatting
                    if (r.action === 'get_top_processes_by_memory' || r.action === 'run_python_code') {
                        lastResult = r;
                    }

                    if (typeof r.output === 'object') {
                        if (r.action === 'run_python_code' || r.action === 'get_top_processes_by_memory') {
                            outputText += formatSystemInfo(r.output, r.args?.description);
                        } else {
                            outputText += JSON.stringify(r.output, null, 2);
                        }
                    } else {
                        outputText += r.output;
                    }
                    if (index < result.results.length - 1) outputText += '\n\n';
                } else if (r.status === 'error' && r.error) {
                    errorText += `❌ ${r.action}: ${r.error}\n`;
                }
            });

            if (successCount === totalCount) {
                addMessage('success', 'Done', outputText || `Completed (${successCount}/${totalCount})`, { results: result.results });
            } else {
                let failureMessage = `Completed with issues (${successCount}/${totalCount})\n\n`;
                if (errorText) {
                    failureMessage += `Errors:\n${errorText}\n`;
                }
                if (outputText) {
                    failureMessage += `\nSuccessful outputs:\n${outputText}`;
                }
                addMessage('warning', 'Done', failureMessage, { results: result.results });
            }
        } else {
            addMessage('error', 'Failed', result.error || 'Execution error.');
        }
    } catch (error) {
        addMessage('error', 'Error', error.message || 'Execution failed.');
    } finally {
        currentPlan = null;
        setProcessing(false);
    }
};

// Reject plan
window.rejectPlan = function() {
    currentPlan = null;
    addMessage('warning', 'Cancelled', 'Action cancelled.');
};

// Handle help
async function handleHelp() {
    try {
        const result = await window.electronAPI.getHelp();

        if (result.success) {
            let helpContent = '<div style="font-size: 14px;">';
            result.help.forEach(section => {
                helpContent += `<strong>${section.title}:</strong><ul style="margin: 5px 0 10px 20px;">`;
                section.examples.forEach(example => {
                    helpContent += `<li>"${example}"</li>`;
                });
                helpContent += '</ul>';
            });
            helpContent += '</div>';
            helpContent += '<div style="margin-top: 10px;"><strong>Special Commands:</strong></div>';
            helpContent += '<ul style="margin: 5px 0 10px 20px;">';
            helpContent += '<li>Click "Help" to show this message</li>';
            helpContent += '<li>Click "View Logs" to see recent actions</li>';
            helpContent += '<li>Click "Clear" to clear the output</li>';
            helpContent += '</ul>';

            addMessage('info', 'Help', helpContent);
        }
    } catch (error) {
        addMessage('error', 'Error', 'Failed to load help information.');
    }
}

// Handle view logs
async function handleViewLogs() {
    setProcessing(true);
    addMessage('info', 'Loading', 'Loading logs...');

    try {
        const result = await window.electronAPI.viewLogs(10);

        if (result.success && result.logs && result.logs.length > 0) {
            let logsContent = '<div class="action-plan">';
            result.logs.forEach(log => {
                const statusColor = log.status === 'success' ? '#4CAF50' : '#f44336';
                logsContent += `<div class="action-item" style="border-left-color: ${statusColor}">`;
                logsContent += `<div class="action-name">${log.action}</div>`;
                logsContent += `<div class="action-args">`;
                logsContent += `Time: ${log.timestamp}<br>`;
                logsContent += `Status: ${log.status}`;
                if (log.error) {
                    logsContent += `<br>Error: ${log.error}`;
                }
                logsContent += '</div></div>';
            });
            logsContent += '</div>';

            addMessage('info', 'Recent Logs', logsContent);
        } else {
            addMessage('warning', 'No Logs', 'No logs found.');
        }
    } catch (error) {
        addMessage('error', 'Error', 'Failed to load logs.');
    } finally {
        setProcessing(false);
    }
}

// Handle clear
function handleClear() {
    outputArea.innerHTML = '';
    currentPlan = null;
}

// Event listeners
sendBtn.addEventListener('click', handleSubmit);
stopBtn.addEventListener('click', handleStop);
helpBtn.addEventListener('click', handleHelp);
logsBtn.addEventListener('click', handleViewLogs);
clearBtn.addEventListener('click', handleClear);

promptInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !isProcessing) {
        handleSubmit();
    }
});

// Initialize - no welcome message
