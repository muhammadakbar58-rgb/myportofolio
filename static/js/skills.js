"use strict";

(() => {
    const section = document.getElementById("skills");
    const form = document.getElementById("skill-form");
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
                const payload = Object.fromEntries(["name", "description", "image"]
                    .map(name => [name, fields.get(name)]));
                await writeSkill(form.dataset.ajaxUrl, form.dataset.apiMethod, payload);
                if (form.dataset.apiMethod === "POST") form.reset();
                showToast("Berhasil", "Skill tersimpan. Gunakan navigasi Skills untuk melihat daftar.", "success");
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
            ? `<a class="button button-secondary" href="${escapeHtml(endpoint(section.dataset.editUrl, skill.id))}">Edit Skill</a>` : "";
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
            grid.replaceChildren(...skills.map(card));
            status.textContent = skills.length ? "" : "Tidak ada skill yang cocok.";
        } catch (failure) {
            if (current.signal.aborted) return;
            status.textContent = failure.message;
            retry.hidden = false;
        } finally {
            if (controller === current) grid.setAttribute("aria-busy", "false");
        }
    }

    grid.addEventListener("click", async event => {
        const button = event.target.closest("button[data-action]");
        if (!button || button.disabled) return;
        const action = button.dataset.action;
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
