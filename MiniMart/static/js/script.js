// script.js
// General small UI helpers used across pages.
// Page-specific logic (POS cart, image previews, delete modal) lives
// as inline <script> blocks in their own templates so each page is
// easy to read on its own during a presentation.

document.addEventListener('DOMContentLoaded', () => {
    // Auto-hide flash messages after a few seconds
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.transition = 'opacity 0.5s ease';
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500);
        }, 4000);
    });
});
