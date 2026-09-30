"use strict";

(() => {
    const section = document.getElementById("projects");
    if (!section) return;

    const grid = document.getElementById("project-list");
    const status = document.getElementById("projects-status");
    const retry = document.getElementById("projects-retry");
    const searchForm = document.getElementById("project-search-form");
    const searchInput = document.getElementById("search-input");
    const projectForm = document.getElementById("project-form");
    const csrfToken = document.querySelector("#projects-csrf input").value;
    const authenticated = section.dataset.authenticated === "true";
    const placeholderId = "00000000-0000-0000-0000-000000000000";
    const SEARCH_DEBOUNCE_DELAY = 300;
    let searchDebounceTimer;
    let projectsAbortController;
    let submitting = false;

    // JSON data must be escaped even when it was saved before form sanitization existed.
    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function safeUrl(value) {
        try {
            const url = new URL(value);
            return ["http:", "https:"].includes(url.protocol) ? url.href : "";
        } catch {
            return "";
        }
    }

    function projectUrl(pattern, id) {
        return escapeHtml(pattern.replace(placeholderId, encodeURIComponent(id)));
    }

    function buildProjectCardElement(item) {
        const project = item.fields;
        const id = escapeHtml(item.pk);
        const title = escapeHtml(project.title);
        const imageUrl = safeUrl(project.project_image_url);
        const linkUrl = safeUrl(project.project_url);
        const starTitle = project.star_count > 0
            ? "Dibintangi oleh " + project.starred_by_names
            : "Jadilah yang pertama memberi star";
        const starContent = `<span aria-hidden="true">&#9733;</span>
            ${project.is_starred ? "Unstar" : "Star"}
            <span class="star-count">${escapeHtml(project.star_count)}</span>`;
        const csrfInput = `<input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(csrfToken)}">`;
        const starHtml = authenticated
            ? `<form method="post" action="${projectUrl(section.dataset.starUrl, item.pk)}" class="star-form">
                ${csrfInput}
                <button type="submit" aria-pressed="${project.is_starred ? "true" : "false"}"
                        class="button button-star${project.is_starred ? " is-starred" : ""}"
                        title="${escapeHtml(starTitle)}">${starContent}</button>
               </form>`
            : `<a href="${escapeHtml(section.dataset.loginUrl + "?next=" + encodeURIComponent(window.location.pathname + window.location.search))}"
                  class="button button-star" title="Login untuk memberi star">${starContent}</a>`;
        const editHtml = section.dataset.editUrl
            ? `<a href="${projectUrl(section.dataset.editUrl, item.pk)}"
                  class="button button-secondary project-edit">Edit Proyek</a>`
            : "";
        // Keep the existing popover confirmation and ordinary CSRF-protected POST.
        const deleteHtml = section.dataset.deleteUrl
            ? `<p class="experience-status">
                <button type="button" class="button button-danger"
                        popovertarget="delete-project-${id}" aria-label="Hapus ${title}"
                        title="Hapus proyek">Hapus Proyek</button>
               </p>
               <div id="delete-project-${id}" class="project-delete-modal" popover="auto"
                    role="dialog" aria-modal="true" aria-labelledby="delete-project-title-${id}">
                <button type="button" class="project-delete-modal__backdrop"
                        popovertarget="delete-project-${id}" popovertargetaction="hide"
                        aria-label="Tutup konfirmasi hapus"></button>
                <div class="project-delete-modal__content">
                    <button type="button" class="project-delete-modal__close"
                            popovertarget="delete-project-${id}" popovertargetaction="hide"
                            aria-label="Tutup konfirmasi hapus">&times;</button>
                    <h2 id="delete-project-title-${id}">Hapus Projek?</h2>
                    <p>Apakah Anda yakin ingin menghapus <strong>${title}</strong>?</p>
                    <div class="project-delete-modal__actions">
                        <button type="button" class="button button-secondary"
                                popovertarget="delete-project-${id}" popovertargetaction="hide">Batal</button>
                        <form method="post" action="${projectUrl(section.dataset.deleteUrl, item.pk)}">
                            ${csrfInput}
                            <button type="submit" class="button button-danger">Ya, Hapus</button>
                        </form>
                    </div>
                </div>
               </div>`
            : "";

        const article = document.createElement("article");
        article.className = "experience-card";
        article.dataset.projectId = item.pk;
        article.innerHTML = `
            ${imageUrl ? `<img src="${escapeHtml(imageUrl)}" alt="Gambar ${title}" class="project-image" loading="lazy">` : ""}
            <h2>${title}</h2>
            <span class="experience-category">${escapeHtml(project.tech_stack)}</span>
            <p class="experience-description">${escapeHtml(project.description)}</p>
            <div class="project-card-actions">
                <div class="project-actions">
                    ${linkUrl ? `<a href="${escapeHtml(linkUrl)}" class="button project-link">Lihat Project</a>` : ""}
                    ${editHtml}
                    ${starHtml}
                    ${deleteHtml}
                </div>
            </div>`;
        return article;
    }

    async function fetchProjects() {
        if (projectsAbortController) projectsAbortController.abort();
        const controller = new AbortController();
        projectsAbortController = controller;
        const query = searchInput.value.trim();
        const url = new URL(section.dataset.projectsUrl, window.location.origin);
        if (query) url.searchParams.set("title", query);
        status.textContent = "Memuat projects...";
        retry.classList.add("hide");
        grid.setAttribute("aria-busy", "true");

        try {
            const response = await fetch(url, {
                headers: { "Accept": "application/json" },
                credentials: "same-origin",
                cache: "no-store",
                signal: controller.signal,
            });
            if (!response.ok) throw new Error("Gagal memuat data (status " + response.status + ").");
            const projects = await response.json();
            if (!Array.isArray(projects)) throw new Error("Format data proyek tidak valid.");
            if (controller.signal.aborted) return;

            const cards = document.createDocumentFragment();
            projects.forEach(project => cards.appendChild(buildProjectCardElement(project)));
            if (!projects.length) {
                const empty = document.createElement("p");
                empty.className = "empty-state";
                empty.textContent = query
                    ? "Tidak ada proyek dengan nama tersebut."
                    : "Belum ada proyek yang ditambahkan.";
                cards.appendChild(empty);
            }
            grid.replaceChildren(cards);
            status.textContent = "";

            // Keep the active search in the address bar and in guest login return links.
            const pageUrl = new URL(window.location.href);
            if (query) pageUrl.searchParams.set("title", query);
            else pageUrl.searchParams.delete("title");
            window.history.replaceState(null, "", pageUrl);
            if (!authenticated) {
                grid.querySelectorAll(".button-star").forEach(link => {
                    link.href = section.dataset.loginUrl + "?next=" +
                        encodeURIComponent(pageUrl.pathname + pageUrl.search);
                });
            }
        } catch (error) {
            if (controller.signal.aborted) return;
            status.textContent = "Gagal memuat data projects. Data sebelumnya tetap ditampilkan. Silakan coba lagi.";
            retry.classList.remove("hide");
        } finally {
            if (projectsAbortController === controller) grid.setAttribute("aria-busy", "false");
        }
    }

    function searchProjects() {
        clearTimeout(searchDebounceTimer);
        return fetchProjects();
    }

    searchInput.addEventListener("input", () => {
        clearTimeout(searchDebounceTimer);
        // Invalidate old results immediately, including during the debounce delay.
        if (projectsAbortController) projectsAbortController.abort();
        searchDebounceTimer = setTimeout(searchProjects, SEARCH_DEBOUNCE_DELAY);
    });
    searchForm.addEventListener("submit", event => {
        event.preventDefault();
        searchProjects();
    });
    retry.addEventListener("click", searchProjects);

    if (projectForm) {
        projectForm.addEventListener("submit", async event => {
            event.preventDefault();
            if (submitting) return;
            submitting = true;
            const submitButton = projectForm.querySelector('button[type="submit"]');
            const errorMessage = document.getElementById("project-form-error");
            submitButton.disabled = true;
            errorMessage.textContent = "";
            projectForm.setAttribute("aria-busy", "true");

            try {
                const response = await fetch(projectForm.dataset.ajaxUrl, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Accept": "application/json",
                        "X-CSRFToken": projectForm.elements.csrfmiddlewaretoken.value,
                    },
                    body: new FormData(projectForm),
                });
                const result = await response.json().catch(() => ({}));
                if (!response.ok) {
                    const errors = result.errors
                        ? Object.values(result.errors).flat().map(error => error.message)
                        : [result.message || "Terjadi kesalahan (status " + response.status + "). Muat ulang halaman jika sesi telah berakhir."];
                    throw new Error(errors.join(" "));
                }
                if (response.redirected || !result.pk) {
                    throw new Error("Respons server tidak valid. Muat ulang halaman dan periksa daftar proyek.");
                }
                projectForm.reset();
                document.getElementById("add-project-modal").hidePopover();
                showToast("Berhasil", "Proyek baru berhasil ditambahkan!", "success");
                await searchProjects();
            } catch (error) {
                const message = error instanceof TypeError
                    ? "Tidak dapat terhubung ke server. Periksa koneksi dan daftar proyek sebelum mencoba lagi."
                    : error.message;
                errorMessage.textContent = message;
                showToast("Gagal menambahkan proyek", message, "error", 6000);
            } finally {
                submitting = false;
                submitButton.disabled = false;
                projectForm.setAttribute("aria-busy", "false");
            }
        });
    }

    fetchProjects();
})();
