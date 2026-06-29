document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const messagesList = document.getElementById('messages-list');
    const emptyState = document.getElementById('empty-state');
    const base64Input = document.getElementById('base64-image');
    const removeImageBtn = document.getElementById('remove-image');

    let currentSessionId = window.location.pathname.split('/').filter(Boolean).pop();
    if (currentSessionId === 'chat' || isNaN(currentSessionId)) {
        currentSessionId = null;
    } else {
        loadSessionMessages(currentSessionId);
    }

    if (!chatForm) return;

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        const image = base64Input.value;
        
        if (!message && !image) return;

        // Hide empty state
        if (emptyState) emptyState.style.display = 'none';

        // Add user message to UI
        appendUserMessage(message, image);
        
        // Clear input and reset textarea height
        messageInput.value = '';
        messageInput.style.height = 'auto';
        if (removeImageBtn) removeImageBtn.click(); // clears image preview
        
        // Show loading skeleton
        const skeletonId = appendLoadingSkeleton();
        scrollToBottom();

        try {
            // Call our existing Django API endpoint
            const res = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    message: message,
                    image: image,
                    session_id: currentSessionId
                })
            });
            
            const data = await res.json();
            
            // Remove skeleton
            const skeleton = document.getElementById(skeletonId);
            if (skeleton) skeleton.remove();
            
            if (res.ok) {
                currentSessionId = data.session_id;
                // Update URL without reloading to reflect session
                window.history.replaceState({}, '', `/chat/${currentSessionId}/`);
                
                appendAiMessage(data.response, data.message_id);
            } else {
                appendError(data.error || 'Failed to get response');
            }
        } catch (error) {
            console.error(error);
            const skeleton = document.getElementById(skeletonId);
            if (skeleton) skeleton.remove();
            appendError('A network error occurred.');
        }
        
        scrollToBottom();
    });

    function appendUserMessage(text, imageSrc) {
        const div = document.createElement('div');
        div.className = 'w-full flex justify-end mb-4';
        
        let content = `<div class="max-w-[80%] bg-chatgpt-bubble text-white rounded-2xl px-4 py-3 shadow-sm border border-chatgpt-border break-words">`;
        if (imageSrc) {
            content += `<img src="${imageSrc}" class="w-48 h-auto rounded-lg mb-2 shadow-md">`;
        }
        if (text) {
            content += `<div>${escapeHtml(text)}</div>`;
        }
        content += `</div>`;
        
        div.innerHTML = content;
        messagesList.appendChild(div);
    }

    function appendAiMessage(rawResponse, messageId = null) {
        const div = document.createElement('div');
        div.className = 'w-full flex justify-start mb-6 text-white text-base';
        
        let content = '';
        try {
            // Try to parse the strict JSON response from the backend
            let response = typeof rawResponse === 'string' ? JSON.parse(rawResponse) : rawResponse;
            
            content = `
                <div class="w-full flex flex-col gap-4">
                    ${response.summary ? `<p class="leading-relaxed">${escapeHtml(response.summary)}</p>` : ''}
                    
                    ${response.fit_score ? `
                        <div class="flex items-center gap-3 my-2">
                            <span class="text-3xl font-bold text-indigo-400">${response.fit_score}</span>
                            <span class="text-xl text-chatgpt-muted font-medium">/10</span>
                        </div>
                    ` : ''}
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 my-2">
                        ${response.what_works && response.what_works.length > 0 ? `
                        <div>
                            <h4 class="font-semibold text-green-400 mb-2 flex items-center gap-2">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                                What works
                            </h4>
                            <ul class="space-y-1 text-sm text-chatgpt-text">
                                ${response.what_works.map(w => `<li>• ${escapeHtml(w)}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}
                        
                        ${response.what_doesnt && response.what_doesnt.length > 0 ? `
                        <div>
                            <h4 class="font-semibold text-red-400 mb-2 flex items-center gap-2">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                                What doesn't
                            </h4>
                            <ul class="space-y-1 text-sm text-chatgpt-text">
                                ${response.what_doesnt.map(w => `<li>• ${escapeHtml(w)}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}
                    </div>
                    
                    ${response.suggestions && response.suggestions.length > 0 ? `
                    <div class="my-2">
                        <h4 class="font-semibold text-indigo-400 mb-2">How to improve</h4>
                        <ul class="space-y-2 text-sm text-chatgpt-text">
                            ${response.suggestions.map(s => `<li class="flex items-start gap-2"><span class="text-indigo-400 mt-1 shrink-0">•</span><span>${escapeHtml(s)}</span></li>`).join('')}
                        </ul>
                    </div>
                    ` : ''}
                    
                    ${response.product_recommendations && response.product_recommendations.length > 0 ? `
                    <div class="mt-4">
                        <h4 class="font-semibold text-white mb-3">Product Picks</h4>
                        <div class="flex overflow-x-auto custom-scrollbar gap-3 pb-2 w-full">
                            ${response.product_recommendations.map(p => `
                                <a href="${escapeHtml(p.url)}" target="_blank" class="shrink-0 bg-chatgpt-bubble border border-chatgpt-border hover:bg-[#383838] transition-colors rounded-xl p-3 w-48 flex flex-col group">
                                    <span class="text-sm font-medium text-white truncate mb-1 group-hover:text-indigo-400 transition-colors">${escapeHtml(p.name)}</span>
                                    <span class="text-xs text-chatgpt-muted truncate">${escapeHtml(p.brand)}</span>
                                    <span class="text-xs text-green-400 mt-2 font-medium">${escapeHtml(p.price)}</span>
                                </a>
                            `).join('')}
                        </div>
                    </div>
                    ` : ''}
                </div>
            `;
            
        } catch(e) {
            // Fallback for non-JSON text
            content = `<div class="leading-relaxed w-full">${escapeHtml(rawResponse).replace(/\\n/g, '<br>')}</div>`;
        }
        
        div.innerHTML = content;
        messagesList.appendChild(div);
    }

    function appendLoadingSkeleton() {
        const id = 'skeleton-' + Date.now();
        const div = document.createElement('div');
        div.id = id;
        div.className = 'w-full flex justify-start mb-6 animate-pulse';
        div.innerHTML = `
            <div class="w-full max-w-xl">
                <div class="h-4 bg-chatgpt-bubble rounded w-3/4 mb-3"></div>
                <div class="h-4 bg-chatgpt-bubble rounded w-1/2 mb-3"></div>
                <div class="h-4 bg-chatgpt-bubble rounded w-5/6"></div>
            </div>
        `;
        messagesList.appendChild(div);
        return id;
    }

    function appendError(msg) {
        const div = document.createElement('div');
        div.className = 'w-full flex justify-start mb-6';
        div.innerHTML = `<div class="text-red-400 text-sm py-2">${escapeHtml(msg)}</div>`;
        messagesList.appendChild(div);
    }

    function scrollToBottom() {
        const container = document.getElementById('messages-container');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
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

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
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
