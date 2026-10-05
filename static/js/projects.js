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
    const technologyFilter = document.getElementById("technology-filter");
    const filterControls = document.getElementById("project-filters");
    const results = document.getElementById("projects-results");
    const emptyState = document.getElementById("projects-empty");
    let cards = [];
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

    function indexCards() {
        cards = [...grid.querySelectorAll("[data-project-id]")].map(card => {
            const title = card.querySelector("h2").textContent.trim();
            const description = card.querySelector(".experience-description");
            const fullDescription = description.textContent.trim();
            const techStack = card.querySelector(".experience-category").textContent.trim();
            const technologies = techStack.split(/[,;|\n]/).map(value => value.trim()).filter(Boolean);

            // Short descriptions remain fully visible without an unnecessary control.
            if (fullDescription.length > 240) {
                const preview = fullDescription.slice(0, 240).trimEnd() + "...";
                description.id = "project-description-" + card.dataset.projectId;
                description.textContent = preview;
                const toggle = document.createElement("button");
                toggle.type = "button";
                toggle.className = "description-toggle";
                toggle.textContent = "Selengkapnya";
                toggle.setAttribute("aria-expanded", "false");
                toggle.setAttribute("aria-controls", description.id);
                toggle.setAttribute("aria-label", "Selengkapnya tentang " + title);
                description.after(toggle);
                toggle.addEventListener("click", () => {
                    const expanded = toggle.getAttribute("aria-expanded") !== "true";
                    toggle.setAttribute("aria-expanded", String(expanded));
                    toggle.textContent = expanded ? "Lebih sedikit" : "Selengkapnya";
                    toggle.setAttribute("aria-label", toggle.textContent + " tentang " + title);
                    description.textContent = expanded ? fullDescription : preview;
                });
            }
            return {
                element: card,
                search: [title, fullDescription, techStack].join(" ").toLowerCase(),
                technologies,
            };
        });

        const selected = technologyFilter.value;
        const technologies = new Map();
        cards.forEach(card => card.technologies.forEach(label => {
            const key = label.toLowerCase();
            if (!technologies.has(key)) technologies.set(key, label);
        }));
        technologyFilter.replaceChildren(new Option("Semua teknologi", ""));
        [...technologies].sort((a, b) => a[1].localeCompare(b[1])).forEach(([key, label]) => {
            technologyFilter.add(new Option(label, key));
        });
        if (technologies.has(selected)) technologyFilter.value = selected;

        grid.querySelectorAll(":scope > .empty-state").forEach(element => element.remove());
        filterControls.hidden = false;
        results.hidden = false;
        applyFilters();
    }

    function applyFilters() {
        const query = searchInput.value.trim().toLowerCase();
        const technology = technologyFilter.value;
        let visible = 0;
        cards.forEach(card => {
            const matches = card.search.includes(query) &&
                (!technology || card.technologies.some(value => value.toLowerCase() === technology));
            card.element.hidden = !matches;
            if (matches) visible += 1;
        });
        results.textContent = visible + " dari " + cards.length + " proyek ditampilkan.";
        emptyState.hidden = visible > 0;
        emptyState.textContent = query || technology
            ? "Tidak ada proyek yang cocok. Coba kata kunci atau teknologi lain."
            : "Belum ada proyek yang ditambahkan.";

        const pageUrl = new URL(window.location.href);
        if (searchInput.value.trim()) pageUrl.searchParams.set("title", searchInput.value.trim());
        else pageUrl.searchParams.delete("title");
        window.history.replaceState(null, "", pageUrl);
        if (!authenticated) {
            grid.querySelectorAll(".button-star").forEach(link => {
                link.href = section.dataset.loginUrl + "?next=" +
                    encodeURIComponent(pageUrl.pathname + pageUrl.search);
            });
        }
    }

    async function fetchProjects() {
        if (projectsAbortController) projectsAbortController.abort();
        const controller = new AbortController();
        projectsAbortController = controller;
        // Fetch the complete collection once, then search/filter locally.
        const url = new URL(section.dataset.projectsUrl, window.location.origin);
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
            grid.replaceChildren(cards);
            indexCards();
            status.textContent = "";
        } catch (error) {
            if (controller.signal.aborted) return;
            status.textContent = "Gagal memuat seluruh proyek. Pencarian hanya berlaku pada data yang sudah tampil. Silakan coba lagi.";
            retry.classList.remove("hide");
        } finally {
            if (projectsAbortController === controller) grid.setAttribute("aria-busy", "false");
        }
    }

    searchInput.placeholder = "Cari nama, deskripsi, atau teknologi";
    searchInput.setAttribute("aria-label", "Cari nama, deskripsi, atau teknologi");
    searchInput.setAttribute("aria-controls", "project-list");
    searchInput.addEventListener("input", applyFilters);
    searchForm.addEventListener("submit", event => {
        event.preventDefault();
        applyFilters();
    });
    technologyFilter.addEventListener("change", applyFilters);
    document.getElementById("projects-reset").addEventListener("click", () => {
        searchInput.value = "";
        technologyFilter.value = "";
        applyFilters();
        searchInput.focus();
    });
    retry.addEventListener("click", fetchProjects);

    if (projectForm) {
        projectForm.addEventListener("submit", async event => {
            event.preventDefault();
            if (submitting || !projectForm.reportValidity()) return;
            submitting = true;
            const submitButton = projectForm.querySelector('button[type="submit"]');
            const errorMessage = document.getElementById("project-form-error");
            const submitLabel = submitButton.textContent;
            submitButton.disabled = true;
            submitButton.textContent = "Menyimpan...";
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
                await fetchProjects();
            } catch (error) {
                const message = error instanceof TypeError
                    ? "Tidak dapat terhubung ke server. Periksa koneksi dan daftar proyek sebelum mencoba lagi."
                    : error.message;
                errorMessage.textContent = message;
                showToast("Gagal menambahkan proyek", message, "error", 6000);
            } finally {
                submitting = false;
                submitButton.disabled = false;
                submitButton.textContent = submitLabel;
                projectForm.setAttribute("aria-busy", "false");
            }
        });
    }

    indexCards();
    fetchProjects();
})();
