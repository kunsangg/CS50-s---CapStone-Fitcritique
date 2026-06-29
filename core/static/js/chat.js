document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const messagesList = document.getElementById('messages-list');
    const emptyState = document.getElementById('empty-state');
    const sendBtn = document.getElementById('send-btn');
    
    // session ID will be managed via the URL or returned from first message
    let currentSessionId = window.location.pathname.split('/').filter(Boolean).pop();
    if (currentSessionId === 'chat' || isNaN(currentSessionId)) {
        currentSessionId = null;
    } else {
        loadSessionMessages(currentSessionId);
    }

    if (!chatForm) return;

    // Handle enter key to submit
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const text = chatInput.value.trim();
        const imageBase64 = window.uploadedImageBase64;
        
        if (!text && !imageBase64) return;
        
        // Hide empty state
        if (emptyState) emptyState.style.display = 'none';
        
        // Disable input
        chatInput.value = '';
        chatInput.style.height = 'auto';
        chatInput.disabled = true;
        sendBtn.disabled = true;
        
        // Clear image upload
        const removeImageBtn = document.getElementById('remove-image-btn');
        if (removeImageBtn) removeImageBtn.click();
        
        // Render optimistic user message
        appendUserMessage(text, imageBase64);
        
        // Append loading skeleton
        const skeletonId = appendLoadingSkeleton();
        
        // Auto scroll
        scrollToBottom();

        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        try {
            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    message: text,
                    image: imageBase64,
                    session_id: currentSessionId
                })
            });
            
            const data = await response.json();
            
            // Remove skeleton
            document.getElementById(skeletonId).remove();
            
            if (response.ok) {
                if (!currentSessionId && data.session_id) {
                    currentSessionId = data.session_id;
                    // Optionally update URL without reloading
                    window.history.replaceState({}, '', `/chat/${currentSessionId}/`);
                }
                
                // Render structured response
                appendAiMessage(data.response, data.message_id);
            } else {
                appendErrorMessage(data.error || "Failed to get response.");
            }
            
        } catch (error) {
            console.error(error);
            document.getElementById(skeletonId).remove();
            appendErrorMessage("Network error occurred.");
        } finally {
            // Re-enable input
            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();
            scrollToBottom();
        }
    });

    function appendUserMessage(text, imageBase64) {
        const div = document.createElement('div');
        div.className = 'flex justify-end';
        
        let content = `<div class="bg-zinc-800 text-zinc-100 px-5 py-3 rounded-2xl rounded-tr-sm max-w-xl shadow-sm">`;
        if (imageBase64) {
            content += `<img src="${imageBase64}" class="w-full max-w-sm rounded-lg mb-2 object-cover border border-zinc-700">`;
        }
        if (text) {
            content += `<p class="whitespace-pre-wrap">${escapeHtml(text)}</p>`;
        }
        content += `</div>`;
        
        div.innerHTML = content;
        messagesList.appendChild(div);
    }

    async function loadSessionMessages(sessionId) {
        if (emptyState) emptyState.style.display = 'none';
        try {
            const response = await fetch(`/api/sessions/${sessionId}/`);
            if (response.ok) {
                const data = await response.json();
                data.messages.forEach(msg => {
                    if (msg.role === 'user') {
                        appendUserMessage(msg.content, msg.image);
                    } else if (msg.role === 'assistant') {
                        appendAiMessage(msg.content, msg.id);
                    }
                });
                scrollToBottom();
            }
        } catch (error) {
            console.error("Failed to load session", error);
        }
    }

    function appendLoadingSkeleton() {
        const id = 'skeleton-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'flex justify-start animate-pulse';
        div.innerHTML = `
            <div class="bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-2xl rounded-tl-sm w-full max-w-2xl p-6 shadow-sm">
                <div class="h-4 bg-zinc-800 rounded w-1/4 mb-4"></div>
                <div class="space-y-3">
                    <div class="h-4 bg-zinc-800 rounded"></div>
                    <div class="h-4 bg-zinc-800 rounded w-5/6"></div>
                </div>
                <div class="mt-6 flex space-x-4">
                    <div class="h-20 w-32 bg-zinc-800 rounded-lg"></div>
                    <div class="h-20 w-32 bg-zinc-800 rounded-lg"></div>
                </div>
            </div>
        `;
        messagesList.appendChild(div);
        return id;
    }

    function appendErrorMessage(msg) {
        const div = document.createElement('div');
        div.className = 'flex justify-start';
        div.innerHTML = `
            <div class="bg-red-500/10 border border-red-500/50 text-red-400 px-5 py-3 rounded-2xl rounded-tl-sm max-w-xl">
                ${escapeHtml(msg)}
            </div>
        `;
        messagesList.appendChild(div);
    }

    function appendAiMessage(responseObj, messageId) {
        const div = document.createElement('div');
        div.className = 'flex justify-start w-full';
        
        // Handle potentially malformed JSON parsing from backend
        let data = responseObj;
        if (typeof data === 'string') {
            try {
                data = JSON.parse(data);
            } catch(e) {
                // If it fails, fallback to simple text
                div.innerHTML = `<div class="bg-zinc-900 border border-zinc-800 text-zinc-100 px-5 py-3 rounded-2xl rounded-tl-sm max-w-2xl whitespace-pre-wrap">${escapeHtml(data)}</div>`;
                messagesList.appendChild(div);
                return;
            }
        }

        // Build the card HTML
        let html = `
        <div class="bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-2xl rounded-tl-sm w-full max-w-3xl p-6 shadow-sm relative group">
            
            <!-- Save Button -->
            <button onclick="saveLook(${messageId}, this)" class="absolute top-4 right-4 text-zinc-500 hover:text-indigo-400 opacity-0 group-hover:opacity-100 transition" title="Save this look">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path></svg>
            </button>
            
            <div class="flex items-start justify-between mb-6 border-b border-zinc-800 pb-4">
                <div>
                    <h3 class="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-1">Overall Verdict</h3>
                    <p class="text-lg text-white leading-relaxed">${escapeHtml(data.summary)}</p>
                </div>
                <div class="ml-4 shrink-0 flex flex-col items-center justify-center w-16 h-16 rounded-full border-2 ${data.fit_score >= 7 ? 'border-green-500/50 text-green-400' : data.fit_score >= 5 ? 'border-yellow-500/50 text-yellow-400' : 'border-red-500/50 text-red-400'}">
                    <span class="text-xl font-bold">${data.fit_score}</span>
                    <span class="text-[10px] text-zinc-500">/10</span>
                </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <!-- What Works -->
                <div>
                    <h4 class="text-sm font-semibold text-zinc-300 flex items-center mb-3">
                        <svg class="w-4 h-4 text-green-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                        What Works
                    </h4>
                    <ul class="space-y-2 text-sm text-zinc-400">
                        ${data.what_works.map(i => `<li>• ${escapeHtml(i)}</li>`).join('')}
                    </ul>
                </div>
                
                <!-- What Doesn't -->
                <div>
                    <h4 class="text-sm font-semibold text-zinc-300 flex items-center mb-3">
                        <svg class="w-4 h-4 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                        Needs Work
                    </h4>
                    <ul class="space-y-2 text-sm text-zinc-400">
                        ${data.what_doesnt.map(i => `<li>• ${escapeHtml(i)}</li>`).join('')}
                    </ul>
                </div>
            </div>
            
            <!-- Suggestions -->
            <div class="mb-6 bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-4">
                <h4 class="text-sm font-semibold text-indigo-400 flex items-center mb-2">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                    Styling Action Items
                </h4>
                <ul class="space-y-2 text-sm text-indigo-200/80">
                    ${data.suggestions.map(i => `<li>→ ${escapeHtml(i)}</li>`).join('')}
                </ul>
            </div>
            
            <!-- Products -->
            ${data.products && data.products.length > 0 ? `
            <div>
                <h4 class="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-3">Recommended Pieces</h4>
                <div class="flex overflow-x-auto pb-4 gap-3 hide-scrollbar">
                    ${data.products.map(p => `
                        <a href="${p.url && p.url !== 'N/A' ? p.url : '#'}" target="_blank" class="shrink-0 w-64 bg-zinc-950 border border-zinc-800 hover:border-zinc-600 rounded-lg p-3 transition flex flex-col group">
                            <span class="font-medium text-white text-sm truncate mb-1 group-hover:text-indigo-400">${escapeHtml(p.name)}</span>
                            <span class="text-xs text-zinc-500 line-clamp-2">${escapeHtml(p.reason)}</span>
                        </a>
                    `).join('')}
                </div>
            </div>
            ` : ''}
        </div>
        `;
        
        div.innerHTML = html;
        messagesList.appendChild(div);
    }

    function scrollToBottom() {
        const container = document.getElementById('chat-container');
        container.scrollTop = container.scrollHeight;
    }

    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        return (unsafe + '')
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }
});

// Global function for the save button inside AI response
async function saveLook(messageId, btnElement) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const sessionId = window.location.pathname.split('/').filter(Boolean).pop();
    
    try {
        const res = await fetch(`/api/sessions/${sessionId}/save/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ message_id: messageId })
        });
        
        if (res.ok) {
            btnElement.classList.remove('text-zinc-500');
            btnElement.classList.add('text-indigo-400');
            btnElement.innerHTML = `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path></svg>`;
        }
    } catch(e) {
        console.error("Save failed", e);
    }
}
