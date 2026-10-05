"use strict";

document.querySelectorAll("[data-enhance-form]").forEach(form => {
    const fields = [...form.querySelectorAll(
        'input:not([type="hidden"]), textarea, select'
    )];
    const counters = [];

    fields.forEach(field => {
        const group = field.closest(".form-group");
        if (!group) return;
        const describedBy = new Set((field.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));

        if (field.maxLength > 0 || field.tagName === "TEXTAREA") {
            const counter = document.createElement("p");
            counter.className = "field-counter";
            counter.id = field.id + "-counter";
            const updateCounter = () => {
                counter.textContent = field.maxLength > 0
                    ? field.value.length + " / " + field.maxLength + " karakter"
                    : field.value.length + " karakter";
            };
            group.appendChild(counter);
            describedBy.add(counter.id);
            field.addEventListener("input", updateCounter);
            counters.push(updateCounter);
            updateCounter();
        }

        const feedback = document.createElement("p");
        feedback.id = field.id + "-feedback";
        feedback.className = "form-error";
        feedback.setAttribute("aria-live", "polite");
        group.appendChild(feedback);
        describedBy.add(feedback.id);
        field.setAttribute("aria-describedby", [...describedBy].join(" "));

        function validate(showFeedback) {
            field.setCustomValidity(field.required && !field.value.trim()
                ? "Field ini wajib diisi dan tidak boleh hanya berisi spasi." : "");
            if (showFeedback) {
                field.setAttribute("aria-invalid", String(!field.validity.valid));
                feedback.textContent = field.validationMessage;
            }
        }
        field.addEventListener("blur", () => validate(true));
        field.addEventListener("invalid", () => validate(true));
        field.addEventListener("input", () => validate(field.getAttribute("aria-invalid") === "true"));
    });

    const submit = form.querySelector('button[type="submit"]');
    const originalLabel = submit?.textContent;

    form.addEventListener("submit", event => {
        // Keep Django as the authority; this only gives earlier browser feedback.
        fields.forEach(field => {
            field.setCustomValidity(field.required && !field.value.trim()
                ? "Field ini wajib diisi dan tidak boleh hanya berisi spasi." : "");
        });
        if (!form.reportValidity()) {
            event.preventDefault();
            event.stopImmediatePropagation();
            return;
        }
        // The existing AJAX handler manages its own pending/error state.
        if (form.dataset.ajaxUrl || !submit) return;
        if (form.getAttribute("aria-busy") === "true") {
            event.preventDefault();
            return;
        }
        form.setAttribute("aria-busy", "true");
        submit.disabled = true;
        submit.textContent = "Menyimpan...";
    });

    form.addEventListener("reset", () => {
        window.setTimeout(() => {
            counters.forEach(update => update());
            fields.forEach(field => {
                field.setCustomValidity("");
                field.removeAttribute("aria-invalid");
                const feedback = document.getElementById(field.id + "-feedback");
                if (feedback) feedback.textContent = "";
            });
        }, 0);
    });

    window.addEventListener("pageshow", () => {
        if (!submit || form.dataset.ajaxUrl) return;
        submit.disabled = false;
        submit.textContent = originalLabel;
        form.removeAttribute("aria-busy");
    });
});
