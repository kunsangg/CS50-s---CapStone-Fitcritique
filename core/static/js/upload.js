document.addEventListener('DOMContentLoaded', () => {
    const triggerUploadBtn = document.getElementById('trigger-upload');
    const imageUploadInput = document.getElementById('image-upload');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removeImageBtn = document.getElementById('remove-image-btn');
    
    // Store the base64 of the image globally so chat.js can read it
    window.uploadedImageBase64 = null;

    if (triggerUploadBtn && imageUploadInput) {
        triggerUploadBtn.addEventListener('click', () => {
            imageUploadInput.click();
        });

        imageUploadInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.src = e.target.result;
                    window.uploadedImageBase64 = e.target.result;
                    imagePreviewContainer.classList.remove('hidden');
                };
                reader.readAsDataURL(file);
            }
        });
    }

    if (removeImageBtn) {
        removeImageBtn.addEventListener('click', () => {
            imageUploadInput.value = '';
            window.uploadedImageBase64 = null;
            imagePreview.src = '';
            imagePreviewContainer.classList.add('hidden');
        });
    }
});
