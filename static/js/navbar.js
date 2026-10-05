"use strict";

(() => {
    const header = document.querySelector(".site-header");
    const toggle = document.getElementById("nav-toggle");
    const nav = document.getElementById("site-nav");
    if (!header || !toggle || !nav) return;

    const mobile = window.matchMedia("(max-width: 1050px)");
    let open = false;

    function setOpen(value, restoreFocus = false) {
        open = value && mobile.matches;
        toggle.setAttribute("aria-expanded", String(open));
        toggle.setAttribute("aria-label", open ? "Tutup navigasi" : "Buka navigasi");
        nav.hidden = mobile.matches && !open;
        if (restoreFocus) toggle.focus();
    }

    function syncLayout() {
        const focusInNav = nav.contains(document.activeElement);
        toggle.hidden = !mobile.matches;
        setOpen(false, mobile.matches && focusInNav);
    }

    toggle.addEventListener("click", () => setOpen(!open));
    nav.addEventListener("click", event => {
        if (mobile.matches && event.target.closest("a")) setOpen(false, true);
    });
    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && open) {
            event.preventDefault();
            setOpen(false, true);
        }
    });
    document.addEventListener("click", event => {
        if (open && !header.contains(event.target)) {
            setOpen(false, nav.contains(document.activeElement));
        }
    });
    header.addEventListener("focusout", event => {
        if (open && event.relatedTarget && !header.contains(event.relatedTarget)) setOpen(false);
    });
    mobile.addEventListener("change", syncLayout);
    syncLayout();
})();
