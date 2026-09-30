"use strict";

let toastTimer;

function showToast(title, message, type = "normal", duration = 3000) {
    const toast = document.getElementById("toast-component");
    if (!toast) return;

    clearTimeout(toastTimer);
    toast.classList.remove("toast-success", "toast-error", "toast-normal");
    toast.classList.add(["success", "error"].includes(type) ? "toast-" + type : "toast-normal");
    document.getElementById("toast-title").textContent = title;
    document.getElementById("toast-message").textContent = message;

    if (typeof toast.showPopover === "function" && !toast.matches(":popover-open")) {
        toast.showPopover();
        void toast.offsetHeight;
    }
    toast.classList.remove("toast-hidden");
    toast.classList.add("toast-show");

    toastTimer = setTimeout(() => {
        toast.classList.remove("toast-show");
        toast.classList.add("toast-hidden");
        toastTimer = setTimeout(() => {
            if (typeof toast.hidePopover === "function") toast.hidePopover();
        }, 300);
    }, duration);
}
