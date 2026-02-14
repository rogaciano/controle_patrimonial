/**
 * Controle Patrimonial - Main JS entry point.
 * Alpine.js + Chart.js + global utilities.
 */

import Alpine from 'alpinejs';

// Expose Alpine globally
window.Alpine = Alpine;

// --- Dark Mode Toggle ---
Alpine.data('darkMode', () => ({
    dark: localStorage.getItem('dark-mode') === 'true' ||
        (!('dark-mode' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches),

    toggle() {
        this.dark = !this.dark;
        localStorage.setItem('dark-mode', this.dark);
        document.documentElement.classList.toggle('dark', this.dark);
    },

    init() {
        document.documentElement.classList.toggle('dark', this.dark);
    },
}));

// --- Flash message auto-dismiss ---
Alpine.data('flashMessage', () => ({
    show: true,
    init() {
        setTimeout(() => { this.show = false; }, 5000);
    },
}));

// --- Confirm delete modal ---
Alpine.data('confirmModal', () => ({
    open: false,
    targetUrl: '',
    targetName: '',

    openModal(url, name) {
        this.targetUrl = url;
        this.targetName = name;
        this.open = true;
    },

    closeModal() {
        this.open = false;
        this.targetUrl = '';
        this.targetName = '';
    },
}));

// Start Alpine
Alpine.start();
