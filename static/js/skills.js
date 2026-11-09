"use strict";

(() => {
    const section = document.getElementById("skills");
    const form = document.getElementById("skill-form");
    const modal = document.getElementById("skill-modal");
    const fieldNames = ["name", "description", "image"];
    const token = document.querySelector("#skills-csrf input, #skill-form input[name=csrfmiddlewaretoken]")?.value;
    const placeholder = "00000000-0000-0000-0000-000000000000";
    const endpoint = (pattern, id) => pattern.replace(placeholder, encodeURIComponent(id));
    const escapeHtml = value => String(value ?? "").replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;").replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;").replaceAll("'", "&#39;");

    async function writeSkill(url, method, payload) {
        const response = await fetch(url, {
            method, credentials: "same-origin",
            headers: { Accept: "application/json", "Content-Type": "application/json", "X-CSRFToken": token },
            body: payload === undefined ? undefined : JSON.stringify(payload),
        });
        if (response.status === 204) return null;
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const messages = Object.values(data).flat().filter(value => typeof value === "string");
            throw new Error(messages.join(" ") || "Permintaan gagal (status " + response.status + ").");
        }
        if (!data.id) throw new Error("Respons server tidak valid. Periksa daftar skill.");
        return data;
    }

    function resetForm() {
        form.reset();
        document.getElementById("skill-form-error").textContent = "";
        fieldNames.forEach(name => {
            const field = form.elements.namedItem(name);
            field.setCustomValidity("");
            field.removeAttribute("aria-invalid");
            const feedback = document.getElementById(field.id + "-feedback");
            if (feedback) feedback.textContent = "";
        });
    }

    function openForm(skill = null) {
        if (!modal || form.getAttribute("aria-busy") === "true") return;
        resetForm();
        form.dataset.ajaxUrl = skill
            ? endpoint(section.dataset.detailUrl, skill.id) : section.dataset.listUrl;
        form.dataset.apiMethod = skill ? "PATCH" : "POST";
        const label = skill ? "Edit Skill" : "Tambah Skill";
        document.getElementById("skill-modal-title").textContent = label;
        form.querySelector('button[type="submit"]').textContent = skill ? "Simpan Perubahan" : label;
        fieldNames.forEach(name => {
            const field = form.elements.namedItem(name);
            field.value = skill ? skill[name] : "";
            field.dispatchEvent(new Event("input", { bubbles: true }));
        });
        modal.showModal();
        form.elements.namedItem("name").focus();
    }

    if (modal) {
        document.getElementById("skill-create")?.addEventListener("click", event => {
            event.preventDefault();
            openForm();
        });
        modal.querySelectorAll("[data-skill-close]").forEach(button => {
            button.addEventListener("click", () => {
                if (form.getAttribute("aria-busy") !== "true") modal.close();
            });
        });
        modal.addEventListener("cancel", event => {
            if (form.getAttribute("aria-busy") === "true") event.preventDefault();
        });
    }

    if (form) {
        form.addEventListener("submit", async event => {
            event.preventDefault();
            if (form.getAttribute("aria-busy") === "true" || !form.reportValidity()) return;
            form.setAttribute("aria-busy", "true");
            const button = form.querySelector('button[type="submit"]');
            const error = document.getElementById("skill-form-error");
            button.disabled = true;
            error.textContent = "";
            try {
                const fields = new FormData(form);
                const payload = Object.fromEntries(fieldNames.map(name => [name, fields.get(name)]));
                const created = form.dataset.apiMethod === "POST";
                await writeSkill(form.dataset.ajaxUrl, form.dataset.apiMethod, payload);
                if (modal) {
                    modal.close();
                    // A newly added item should be visible even after a previous search.
                    if (created) search.value = "";
                    clearTimeout(timer);
                    await fetchSkills();
                } else if (created) {
                    resetForm();
                }
                showToast("Berhasil", created ? "Skill berhasil ditambahkan." : "Skill berhasil diperbarui.", "success");
            } catch (failure) {
                error.textContent = failure.message;
                showToast("Gagal menyimpan skill", failure.message, "error");
            } finally {
                form.setAttribute("aria-busy", "false");
                button.disabled = false;
            }
        });
    }
    if (!section) return;

    const grid = document.getElementById("skill-list");
    const status = document.getElementById("skills-status");
    const retry = document.getElementById("skills-retry");
    const searchForm = document.getElementById("skill-search-form");
    const search = document.getElementById("skill-search");
    let controller;
    let timer;
    const items = new Map();
    searchForm.hidden = false;

    function card(skill) {
        const article = document.createElement("article");
        article.className = "experience-card";
        const id = escapeHtml(skill.id);
        const name = escapeHtml(skill.name);
        const image = section.dataset.staticUrl + skill.image.split("/").map(encodeURIComponent).join("/");
        const star = section.dataset.authenticated === "true"
            ? `<button type="button" data-action="star" data-id="${id}"
                 aria-pressed="${skill.is_starred ? "true" : "false"}"
                 class="button button-star${skill.is_starred ? " is-starred" : ""}"
                 title="${escapeHtml(skill.starred_by_names)}"><span aria-hidden="true">&#9733;</span>
                 ${skill.is_starred ? "Unstar" : "Star"} <span class="star-count">${escapeHtml(skill.star_count)}</span></button>`
            : `<a class="button button-star" href="${escapeHtml(section.dataset.loginUrl + "?next=" + encodeURIComponent(window.location.pathname + window.location.search))}">
                 <span aria-hidden="true">&#9733;</span> Star <span class="star-count">${escapeHtml(skill.star_count)}</span></a>`;
        const edit = section.dataset.editor === "true"
            ? `<a class="button button-secondary" data-action="edit" data-id="${id}" aria-haspopup="dialog" aria-controls="skill-modal" href="${escapeHtml(endpoint(section.dataset.editUrl, skill.id))}">Edit Skill</a>` : "";
        const remove = section.dataset.owner === "true"
            ? `<p class="experience-status"><button type="button" class="button button-danger"
                 popovertarget="delete-skill-${id}" aria-label="Hapus ${name}">Hapus Skill</button></p>
               <div id="delete-skill-${id}" class="project-delete-modal" popover="auto" role="dialog"
                    aria-modal="true" aria-labelledby="delete-skill-title-${id}">
                 <button type="button" class="project-delete-modal__backdrop" popovertarget="delete-skill-${id}"
                         popovertargetaction="hide" aria-label="Tutup konfirmasi hapus"></button>
                 <div class="project-delete-modal__content">
                   <button type="button" class="project-delete-modal__close" popovertarget="delete-skill-${id}"
                           popovertargetaction="hide" aria-label="Tutup konfirmasi hapus">&times;</button>
                   <h2 id="delete-skill-title-${id}">Hapus Skill?</h2>
                   <p>Apakah Anda yakin ingin menghapus <strong>${name}</strong>?</p>
                   <div class="project-delete-modal__actions">
                     <button type="button" class="button button-secondary" popovertarget="delete-skill-${id}"
                             popovertargetaction="hide">Batal</button>
                     <button type="button" class="button button-danger" data-action="delete" data-id="${id}">Ya, Hapus</button>
                   </div>
                 </div>
               </div>` : "";
        article.innerHTML = `<img class="skill-image" src="${escapeHtml(image)}" alt="${name}" width="64" height="64" loading="lazy">
            <h2>${name}</h2><p>${escapeHtml(skill.description)}</p>
            <div class="project-card-actions"><div class="project-actions">${edit}${star}${remove}</div></div>`;
        return article;
    }

    async function fetchSkills() {
        if (controller) controller.abort();
        const current = new AbortController();
        controller = current;
        status.textContent = "Memuat skills...";
        retry.hidden = true;
        grid.setAttribute("aria-busy", "true");
        try {
            const url = new URL(section.dataset.listUrl, window.location.origin);
            if (search.value.trim()) url.searchParams.set("name", search.value.trim());
            const response = await fetch(url, {
                headers: { Accept: "application/json" }, credentials: "same-origin",
                cache: "no-store", signal: current.signal,
            });
            if (!response.ok) throw new Error("Gagal memuat skills (status " + response.status + ").");
            const skills = await response.json();
            if (!Array.isArray(skills)) throw new Error("Format data skill tidak valid.");
            if (current.signal.aborted) return;
            const cards = skills.map(card);
            items.clear();
            skills.forEach(skill => items.set(String(skill.id), skill));
            grid.replaceChildren(...cards);
            status.textContent = skills.length ? "" : search.value.trim()
                ? "Tidak ada skill yang cocok." : "Belum ada skill yang ditambahkan.";
        } catch (failure) {
            if (current.signal.aborted) return;
            status.textContent = failure.message;
            retry.hidden = false;
            showToast("Gagal memuat skills", failure.message, "error");
        } finally {
            if (controller === current) grid.setAttribute("aria-busy", "false");
        }
    }

    grid.addEventListener("click", async event => {
        const button = event.target.closest("[data-action]");
        if (!button || button.disabled) return;
        const action = button.dataset.action;
        if (action === "edit" && modal) {
            event.preventDefault();
            const skill = items.get(button.dataset.id);
            if (skill) openForm(skill);
            return;
        }
        if (!["star", "delete"].includes(action)) return;
        button.disabled = true;
        try {
            const pattern = action === "star" ? section.dataset.starUrl : section.dataset.detailUrl;
            await writeSkill(endpoint(pattern, button.dataset.id), action === "star" ? "POST" : "DELETE");
            const popover = button.closest("[popover]");
            if (popover) popover.hidePopover();
            showToast("Berhasil", action === "star" ? "Star diperbarui." : "Skill dihapus.", "success");
            await fetchSkills();
        } catch (failure) {
            showToast("Permintaan gagal", failure.message, "error");
        } finally {
            button.disabled = false;
        }
    });
    search.addEventListener("input", () => {
        clearTimeout(timer);
        if (controller) controller.abort();
        timer = setTimeout(fetchSkills, 300);
    });
    searchForm.addEventListener("submit", event => {
        event.preventDefault();
        clearTimeout(timer);
        fetchSkills();
    });
    retry.addEventListener("click", fetchSkills);
    fetchSkills();
})();
