document.addEventListener('DOMContentLoaded', () => {
    // 1. Textarea Auto-Resize & Send Button State
    const textarea = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    
    if (textarea && sendBtn) {
        textarea.addEventListener('input', function() {
            // Auto resize
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            
            // Send button state
            const hasText = this.value.trim().length > 0;
            const hasImage = document.getElementById('base64-image').value.length > 0;
            
            if (hasText || hasImage) {
                sendBtn.removeAttribute('disabled');
                sendBtn.classList.remove('bg-chatgpt-border', 'text-chatgpt-muted');
                sendBtn.classList.add('bg-white', 'text-black', 'hover:bg-zinc-200'); // Or indigo: bg-indigo-500 text-white
            } else {
                sendBtn.setAttribute('disabled', 'true');
                sendBtn.classList.remove('bg-white', 'text-black', 'hover:bg-zinc-200', 'bg-indigo-500', 'text-white');
                sendBtn.classList.add('bg-chatgpt-border', 'text-chatgpt-muted');
            }
        });

        // Submit on Enter (prevent default newline), allow Shift+Enter for newline
        textarea.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!sendBtn.hasAttribute('disabled')) {
                    document.getElementById('chat-form').dispatchEvent(new Event('submit'));
                }
            }
        });
    }

    // 2. Suggestion Chips logic
    const chips = document.querySelectorAll('.suggestion-chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            if (textarea) {
                textarea.value = chip.querySelector('span').innerText;
                textarea.dispatchEvent(new Event('input')); // Trigger resize and btn state
                if (!sendBtn.hasAttribute('disabled')) {
                    document.getElementById('chat-form').dispatchEvent(new Event('submit'));
                }
            }
        });
    });

    // 3. Image Upload Preview Logic
    const attachBtn = document.getElementById('attach-btn');
    const imageInput = document.getElementById('image-input');
    const previewContainer = document.getElementById('preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removeBtn = document.getElementById('remove-image');
    const base64Input = document.getElementById('base64-image');
    
    if (attachBtn && imageInput) {
        attachBtn.addEventListener('click', () => imageInput.click());
        
        imageInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    imagePreview.src = e.target.result;
                    base64Input.value = e.target.result;
                    previewContainer.classList.remove('hidden');
                    if (textarea) textarea.dispatchEvent(new Event('input')); // Trigger btn state
                };
                reader.readAsDataURL(file);
            }
        });
        
        removeBtn.addEventListener('click', () => {
            imageInput.value = '';
            base64Input.value = '';
            imagePreview.src = '#';
            previewContainer.classList.add('hidden');
            if (textarea) textarea.dispatchEvent(new Event('input')); // Trigger btn state
        });
    }
});
