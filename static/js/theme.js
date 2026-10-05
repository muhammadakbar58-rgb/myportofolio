"use strict";

(() => {
    const root = document.documentElement;
    const preference = window.matchMedia("(prefers-color-scheme: dark)");
    const storageKey = "portfolio-theme";
    let savedTheme = null;
    let toggle;

    try {
        const stored = localStorage.getItem(storageKey);
        if (stored === "dark" || stored === "light") savedTheme = stored;
    } catch {
        // Theme switching still works when storage is unavailable.
    }

    function applyTheme(theme) {
        root.dataset.theme = theme;
        if (toggle) {
            const label = theme === "dark" ? "Mode terang" : "Mode gelap";
            toggle.textContent = label;
            toggle.setAttribute("aria-label", label);
        }
    }

    applyTheme(savedTheme || (preference.matches ? "dark" : "light"));

    function initializeToggle() {
        toggle = document.getElementById("theme-toggle");
        if (!toggle) return;
        toggle.hidden = false;
        applyTheme(root.dataset.theme);
        toggle.addEventListener("click", () => {
            savedTheme = root.dataset.theme === "dark" ? "light" : "dark";
            applyTheme(savedTheme);
            try {
                localStorage.setItem(storageKey, savedTheme);
            } catch {
                // Keep the selected theme for this page even without storage.
            }
        });
    }

    // Also initialize if this file is loaded after DOMContentLoaded.
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initializeToggle, { once: true });
    } else {
        initializeToggle();
    }

    preference.addEventListener("change", event => {
        if (!savedTheme) applyTheme(event.matches ? "dark" : "light");
    });

    window.addEventListener("storage", event => {
        if (event.key !== storageKey && event.key !== null) return;
        savedTheme = ["dark", "light"].includes(event.newValue) ? event.newValue : null;
        applyTheme(savedTheme || (preference.matches ? "dark" : "light"));
    });
})();
