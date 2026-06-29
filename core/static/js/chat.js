const composer = document.getElementById("composer-input");
const sendBtn = document.getElementById("send-btn");
const messagesContainer = document.getElementById("messages");
const imageInput = document.getElementById("image-input");
const imagePreview = document.getElementById("image-preview");
const imagePreviewImg = document.getElementById("preview-img");
const removeImageBtn = document.getElementById("remove-image");
const emptyState = document.getElementById("empty-state");

let currentSessionId = null;
let selectedImage = null;

// Send button active state
composer.addEventListener("input", () => {
    sendBtn.style.backgroundColor = 
        composer.value.trim() ? "#6366f1" : "#3f3f3f";
    autoResize();
});

function autoResize() {
    composer.style.height = "auto";
    composer.style.height = composer.scrollHeight + "px";
}

// Image selection
imageInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    selectedImage = file;
    const url = URL.createObjectURL(file);
    imagePreviewImg.src = url;
    imagePreview.classList.remove("hidden");
});

removeImageBtn.addEventListener("click", () => {
    selectedImage = null;
    imageInput.value = "";
    imagePreview.classList.add("hidden");
});

// Send on Enter (Shift+Enter for newline)
composer.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

sendBtn.addEventListener("click", sendMessage);

// Suggestion chips
document.querySelectorAll(".suggestion-chip").forEach(chip => {
    chip.addEventListener("click", () => {
        composer.value = chip.textContent.trim();
        sendMessage();
    });
});

async function sendMessage() {
    const text = composer.value.trim();
    if (!text && !selectedImage) return;

    // Hide empty state
    if (emptyState) emptyState.classList.add("hidden");

    // Render user message
    appendUserMessage(text, selectedImage);

    // Reset composer
    composer.value = "";
    composer.style.height = "auto";
    sendBtn.style.backgroundColor = "#3f3f3f";

    // Show loading
    const loadingEl = appendLoading();

    // Build form data
    const formData = new FormData();
    formData.append("message", text);
    if (currentSessionId) {
        formData.append("session_id", currentSessionId);
    }
    if (selectedImage) {
        formData.append("image", selectedImage);
    }

    // Reset image
    selectedImage = null;
    imageInput.value = "";
    imagePreview.classList.add("hidden");

    try {
        const res = await fetch("/api/chat/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: formData
        });

        const data = await res.json();
        loadingEl.remove();

        if (data.error) {
            appendError(data.error);
            return;
        }

        currentSessionId = data.session_id;
        appendCritiqueCard(data.critique, data.message_id);

    } catch (err) {
        loadingEl.remove();
        appendError("Something went wrong. Try again.");
    }
}

function appendUserMessage(text, image) {
    const div = document.createElement("div");
    div.className = "flex justify-end mb-6";
    
    let imageHtml = "";
    if (image) {
        const url = URL.createObjectURL(image);
        imageHtml = `<img src="${url}" 
                         class="w-48 h-48 object-cover rounded-xl mb-2" />`;
    }

    div.innerHTML = `
        <div class="max-w-lg bg-[#2f2f2f] rounded-2xl px-4 py-3 text-[#ececec]">
            ${imageHtml}
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    messagesContainer.appendChild(div);
    scrollToBottom();
}

function appendLoading() {
    const div = document.createElement("div");
    div.className = "flex justify-start mb-6";
    div.innerHTML = `
        <div class="flex gap-1 items-center py-3">
            <span class="w-2 h-2 bg-[#8e8ea0] rounded-full 
                         animate-bounce [animation-delay:0ms]"></span>
            <span class="w-2 h-2 bg-[#8e8ea0] rounded-full 
                         animate-bounce [animation-delay:150ms]"></span>
            <span class="w-2 h-2 bg-[#8e8ea0] rounded-full 
                         animate-bounce [animation-delay:300ms]"></span>
        </div>
    `;
    messagesContainer.appendChild(div);
    scrollToBottom();
    return div;
}

function appendCritiqueCard(critique, messageId) {
    const div = document.createElement("div");
    div.className = "mb-8 text-[#ececec] max-w-2xl";

    const worksHtml = critique.what_works.map(w => `
        <li class="flex gap-2 items-start">
            <span class="text-green-400 mt-0.5">✓</span>
            <span>${escapeHtml(w)}</span>
        </li>
    `).join("");

    const doesntHtml = critique.what_doesnt.map(w => `
        <li class="flex gap-2 items-start">
            <span class="text-red-400 mt-0.5">✗</span>
            <span>${escapeHtml(w)}</span>
        </li>
    `).join("");

    const suggestionsHtml = critique.suggestions.map(s => `
        <li class="flex gap-2 items-start">
            <span class="text-indigo-400 mt-0.5">→</span>
            <span>${escapeHtml(s)}</span>
        </li>
    `).join("");

    const productsHtml = critique.products.map(p => `
        <span class="inline-block bg-[#2f2f2f] border border-[#3f3f3f] 
                     rounded-full px-4 py-1.5 text-sm text-[#ececec] 
                     whitespace-nowrap">
            ${escapeHtml(p.name)}
            <span class="text-[#8e8ea0] ml-1 text-xs">
                — ${escapeHtml(p.reason)}
            </span>
        </span>
    `).join("");

    div.innerHTML = `
        <div class="mb-4 flex items-center gap-3">
            <span class="text-5xl font-bold text-indigo-400">
                ${critique.fit_score}
            </span>
            <span class="text-[#8e8ea0] text-lg">/10</span>
        </div>

        <p class="text-[#ececec] mb-6 leading-relaxed">
            ${escapeHtml(critique.summary)}
        </p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
                <p class="text-xs uppercase tracking-widest text-[#8e8ea0] 
                          mb-3">What Works</p>
                <ul class="space-y-2 text-sm">${worksHtml}</ul>
            </div>
            <div>
                <p class="text-xs uppercase tracking-widest text-[#8e8ea0] 
                          mb-3">What Doesn't</p>
                <ul class="space-y-2 text-sm">${doesntHtml}</ul>
            </div>
        </div>

        <div class="mb-6">
            <p class="text-xs uppercase tracking-widest text-[#8e8ea0] 
                      mb-3">Suggestions</p>
            <ul class="space-y-2 text-sm">${suggestionsHtml}</ul>
        </div>

        <div>
            <p class="text-xs uppercase tracking-widest text-[#8e8ea0] 
                      mb-3">Product Picks</p>
            <div class="flex flex-wrap gap-2">${productsHtml}</div>
        </div>

        <div class="mt-6 border-t border-[#3f3f3f] pt-4">
            <button onclick="saveThisLook(this)" 
                    data-message-id="${messageId}"
                    class="text-xs text-[#a1a1aa] hover:text-cyan-400 
                           transition-colors font-medium">
                + Save this look
            </button>
        </div>
    `;

    messagesContainer.appendChild(div);
    scrollToBottom();
}

function appendError(msg) {
    const div = document.createElement("div");
    div.className = "flex justify-start mb-6";
    div.innerHTML = `
        <div class="max-w-lg bg-[#2f2f2f] border border-red-500/30 rounded-2xl px-4 py-3 text-red-400 text-sm">
            ${escapeHtml(msg)}
        </div>
    `;
    messagesContainer.appendChild(div);
    scrollToBottom();
}

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
}

async function saveThisLook(btn) {
    const messageId = btn.dataset.messageId;
    if (!messageId) return;
    
    try {
        const res = await fetch("/api/save-look/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({ message_id: messageId })
        });
        const data = await res.json();
        if (data.saved) {
            btn.textContent = "✓ Saved";
            btn.classList.add("text-cyan-400");
            btn.disabled = true;
        }
    } catch (err) {
        btn.textContent = "Failed to save";
    }
}
