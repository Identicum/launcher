// Admin page: manage links through /api/admin/links and import/export.
// DOM is built with textContent only, so stored values are never interpreted as HTML.
(function () {
  const script = document.currentScript;
  const PUBLIC_ROLE = script.dataset.publicRole;
  const ICONS_URL = script.dataset.iconsUrl;
  const STYLES = { s: "solid", r: "regular", b: "brands" };
  const MAX_ICON_RESULTS = 240;

  const $ = (id) => document.getElementById(id);
  const linkModal = new bootstrap.Modal($("link-modal"));
  const deleteModal = new bootstrap.Modal($("delete-modal"));
  const importModal = new bootstrap.Modal($("import-modal"));
  const toast = new bootstrap.Toast($("toast"), { delay: 4000 });

  let links = [];
  let editing = null; // link being edited, null when adding
  let deleting = null;
  let roles = []; // roles in the form
  let icons = null; // icon index, loaded on first use

  // ---------- helpers ----------

  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (key === "class") node.className = value;
      else if (key === "text") node.textContent = value;
      else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
      else if (value !== null && value !== undefined && value !== false) node.setAttribute(key, value);
    }
    children.flat().forEach((child) => child && node.append(child));
    return node;
  }

  async function api(method, url, body) {
    const options = { method, headers: { Accept: "application/json" } };
    if (body instanceof FormData) options.body = body;
    else if (body !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    const response = await fetch(url, options);
    const data = response.status === 204 ? null : await response.json().catch(() => null);
    if (!response.ok) throw { status: response.status, data };
    return data;
  }

  function errorMessage(error) {
    if (error && error.data && typeof error.data.detail === "string") return error.data.detail;
    if (error && error.status) return `The server answered with HTTP ${error.status}.`;
    return "Could not reach the server.";
  }

  function notify(message, variant = "success") {
    $("toast").className = `toast align-items-center border-0 text-bg-${variant}`;
    $("toast-body").textContent = message;
    toast.show();
  }

  function safeHref(url) {
    return /^\s*(javascript|data|vbscript):/i.test(url) ? null : url;
  }

  function isSafeColor(color) {
    return /^[#\w\s(),.%-]*$/.test(color || "");
  }

  function tileIcon(link) {
    const icon = el("span", { class: "tile-icon" }, el("i", { class: link.icon || "fa-solid fa-link", "aria-hidden": "true" }));
    if (link.color && isSafeColor(link.color)) icon.style.setProperty("--tile-color", link.color);
    return icon;
  }

  function roleBadge(name) {
    return el("span", { class: `badge rounded-pill role-badge${name === PUBLIC_ROLE ? " is-public" : ""}`, text: name });
  }

  // ---------- list ----------

  async function load() {
    try {
      links = await api("GET", "/api/admin/links");
    } catch (error) {
      notify(`Could not load links: ${errorMessage(error)}`, "danger");
      links = [];
    }
    render();
    const suggestions = [...new Set(links.flatMap((link) => link.roles))].sort();
    $("role-suggestions").replaceChildren(...suggestions.map((name) => el("option", { value: name })));
  }

  function render() {
    const words = $("filter").value.toLowerCase().split(/\s+/).filter(Boolean);
    const shown = links.filter((link) => {
      const text = [link.display, link.target, ...link.roles].join(" ").toLowerCase();
      return words.every((word) => text.includes(word));
    });
    $("link-count").textContent = words.length ? `${shown.length} of ${links.length}` : links.length;
    $("links").replaceChildren(...shown.map(row));
    $("links-empty").classList.toggle("d-none", shown.length > 0);
    $("links-empty").querySelector("[data-empty-text]").textContent = links.length
      ? "No links match the filter."
      : "No links yet. Add one, or import a JSON file.";
  }

  function row(link) {
    const roleCell = link.roles.length
      ? el("div", { class: "d-flex flex-wrap gap-1" }, link.roles.map(roleBadge))
      : el("span", { class: "badge rounded-pill text-bg-warning", title: "Nobody sees a link without roles" }, el("i", { class: "fa-solid fa-eye-slash me-1" }), "No roles");
    return el(
      "tr",
      {},
      el(
        "td",
        { class: "ps-3" },
        el(
          "div",
          { class: "d-flex align-items-center gap-3" },
          tileIcon(link),
          el("div", { class: "min-w-0" }, el("div", { class: "fw-medium", text: link.display }), el("div", { class: "d-md-none small text-body-secondary text-truncate", text: link.target }))
        )
      ),
      el("td", { class: "d-none d-md-table-cell" }, el("div", { class: "target text-truncate small" }, el("a", { href: safeHref(link.target), target: "_blank", rel: "noopener", class: "link-secondary link-underline-opacity-0 link-underline-opacity-75-hover", text: link.target, title: link.target }))),
      el("td", {}, roleCell),
      el(
        "td",
        { class: "text-end pe-3 text-nowrap" },
        el("button", { type: "button", class: "btn btn-sm btn-link link-secondary", title: `Edit ${link.display}`, "aria-label": `Edit ${link.display}`, onclick: () => openForm(link) }, el("i", { class: "fa-solid fa-pen" })),
        el("button", { type: "button", class: "btn btn-sm btn-link link-danger", title: `Delete ${link.display}`, "aria-label": `Delete ${link.display}`, onclick: () => openDelete(link) }, el("i", { class: "fa-solid fa-trash" }))
      )
    );
  }

  $("filter").addEventListener("input", render);

  // ---------- add / edit ----------

  const form = $("link-form");
  const field = (name) => form.elements[name];

  function openForm(link) {
    editing = link;
    form.reset();
    clearErrors();
    $("link-modal-title").textContent = link ? `Edit ${link.display}` : "Add link";
    field("display").value = link ? link.display : "";
    field("target").value = link ? link.target : "";
    field("icon").value = link ? link.icon || "" : "";
    field("color").value = link ? link.color || "" : "";
    roles = link ? [...link.roles] : [];
    $("f-role-input").value = "";
    syncColorPicker();
    renderChips();
    updatePreview();
    toggleIconPicker(false);
    linkModal.show();
  }

  $("add-link").addEventListener("click", () => openForm(null));
  $("link-modal").addEventListener("shown.bs.modal", () => field("display").focus());

  function updatePreview() {
    const preview = $("tile-preview");
    const icon = field("icon").value.trim() || "fa-solid fa-link";
    preview.querySelector(".tile-icon i").className = icon;
    $("f-icon-preview").className = icon;
    preview.querySelector(".tile-label").textContent = field("display").value.trim() || "Name";
    const color = field("color").value.trim();
    if (color && isSafeColor(color)) preview.style.setProperty("--tile-color", color);
    else preview.style.removeProperty("--tile-color");
  }

  ["display", "icon", "color"].forEach((name) => field(name).addEventListener("input", updatePreview));

  function syncColorPicker() {
    const color = field("color").value.trim();
    if (/^#[0-9a-f]{6}$/i.test(color)) $("f-color-picker").value = color;
    else if (/^#[0-9a-f]{3}$/i.test(color)) $("f-color-picker").value = "#" + [...color.slice(1)].map((c) => c + c).join("");
  }

  field("color").addEventListener("input", syncColorPicker);
  $("f-color-picker").addEventListener("input", () => {
    field("color").value = $("f-color-picker").value;
    updatePreview();
  });

  // roles as chips
  function renderChips() {
    $("role-chips").replaceChildren(
      ...roles.map((name, index) =>
        el(
          "span",
          { class: `role-chip badge role-badge${name === PUBLIC_ROLE ? " is-public" : ""}` },
          el("span", { text: name }),
          el("button", { type: "button", "aria-label": `Remove ${name}`, onclick: () => { roles.splice(index, 1); renderChips(); } }, "×")
        )
      )
    );
  }

  function addRole(value) {
    value
      .split(/[|,]/)
      .map((name) => name.trim())
      .filter((name) => name && !roles.includes(name))
      .forEach((name) => roles.push(name));
    renderChips();
  }

  const roleInput = $("f-role-input");
  roleInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      addRole(roleInput.value);
      roleInput.value = "";
    } else if (event.key === "Backspace" && !roleInput.value && roles.length) {
      roles.pop();
      renderChips();
    }
  });
  roleInput.addEventListener("change", () => {
    // picking a datalist suggestion
    if (roleInput.value && [...$("role-suggestions").options].some((o) => o.value === roleInput.value)) {
      addRole(roleInput.value);
      roleInput.value = "";
    }
  });
  $("role-box").addEventListener("click", (event) => event.target === $("role-box") && roleInput.focus());
  $("add-public").addEventListener("click", () => addRole(PUBLIC_ROLE));

  // icon picker
  function toggleIconPicker(show) {
    $("icon-picker").classList.toggle("d-none", !show);
    $("browse-icons").setAttribute("aria-expanded", String(show));
    if (show) {
      $("icon-search").focus();
      loadIcons();
    }
  }

  $("browse-icons").addEventListener("click", () => toggleIconPicker($("icon-picker").classList.contains("d-none")));

  async function loadIcons() {
    if (!icons) {
      $("icon-status").textContent = "Loading icons…";
      try {
        icons = (await (await fetch(ICONS_URL)).json()).map(([name, styles, terms]) => ({ name, styles, terms: `${name} ${terms}`.toLowerCase() }));
      } catch (e) {
        $("icon-status").textContent = "Could not load the icon list. Type the icon classes instead.";
        return;
      }
    }
    renderIcons();
  }

  function renderIcons() {
    const words = $("icon-search").value.toLowerCase().split(/\s+/).filter(Boolean);
    const current = field("icon").value.trim();
    const matches = [];
    for (const icon of icons) {
      if (!words.every((word) => icon.terms.includes(word))) continue;
      for (const code of icon.styles) matches.push(`fa-${STYLES[code]} fa-${icon.name}`);
      if (matches.length >= MAX_ICON_RESULTS) break;
    }
    $("icon-grid").replaceChildren(
      ...matches.map((classes) =>
        el(
          "button",
          { type: "button", class: classes === current ? "selected" : "", title: classes, "aria-label": classes, role: "option", onclick: () => pickIcon(classes) },
          el("i", { class: classes, "aria-hidden": "true" })
        )
      )
    );
    $("icon-status").textContent = matches.length
      ? matches.length >= MAX_ICON_RESULTS ? `Showing the first ${MAX_ICON_RESULTS} icons. Refine the search to see more.` : `${matches.length} icons`
      : "No icons match.";
  }

  function pickIcon(classes) {
    field("icon").value = classes;
    updatePreview();
    toggleIconPicker(false);
  }

  $("icon-search").addEventListener("input", () => icons && renderIcons());

  // save
  function clearErrors() {
    form.querySelectorAll(".is-invalid").forEach((node) => node.classList.remove("is-invalid"));
    form.querySelectorAll("[data-error]").forEach((node) => (node.textContent = ""));
    $("link-form-error").classList.add("d-none");
  }

  function showErrors(error) {
    const details = error && error.data && Array.isArray(error.data.detail) ? error.data.detail : null;
    if (!details) {
      $("link-form-error").textContent = errorMessage(error);
      $("link-form-error").classList.remove("d-none");
      return;
    }
    for (const detail of details) {
      const name = detail.loc[1];
      const message = detail.msg.replace(/^Value error, /, "");
      const target = form.querySelector(`[data-error="${name}"]`);
      if (target) {
        target.textContent = message;
        if (field(name)) field(name).classList.add("is-invalid");
      } else {
        $("link-form-error").textContent = message;
        $("link-form-error").classList.remove("d-none");
      }
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors();
    addRole(roleInput.value); // a role typed but not confirmed with Enter
    roleInput.value = "";
    const body = {
      display: field("display").value,
      target: field("target").value,
      icon: field("icon").value,
      color: field("color").value,
      type: editing ? editing.type : "html",
      roles,
    };
    $("link-save").disabled = true;
    try {
      const saved = editing ? await api("PUT", `/api/admin/links/${editing.id}`, body) : await api("POST", "/api/admin/links", body);
      linkModal.hide();
      notify(`${saved.display} ${editing ? "updated" : "added"}.`);
      await load();
    } catch (error) {
      showErrors(error);
    } finally {
      $("link-save").disabled = false;
    }
  });

  // ---------- delete ----------

  function openDelete(link) {
    deleting = link;
    $("delete-name").textContent = link.display;
    deleteModal.show();
  }

  $("delete-confirm").addEventListener("click", async () => {
    $("delete-confirm").disabled = true;
    try {
      await api("DELETE", `/api/admin/links/${deleting.id}`);
      deleteModal.hide();
      notify(`${deleting.display} deleted.`);
      await load();
    } catch (error) {
      notify(`Could not delete: ${errorMessage(error)}`, "danger");
    } finally {
      $("delete-confirm").disabled = false;
    }
  });

  // ---------- import ----------

  const importForm = $("import-form");
  importForm.addEventListener("change", () => {
    $("replace-warning").classList.toggle("d-none", importForm.elements.mode.value !== "replace");
  });
  $("import-modal").addEventListener("show.bs.modal", () => {
    importForm.reset();
    $("replace-warning").classList.add("d-none");
    $("import-error").classList.add("d-none");
  });

  importForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    $("import-error").classList.add("d-none");
    $("import-submit").disabled = true;
    try {
      const result = await api("POST", "/admin/data/import", new FormData(importForm));
      importModal.hide();
      const parts = [`${result.created} added`];
      if (result.updated) parts.push(`${result.updated} updated`);
      if (result.skipped) parts.push(`${result.skipped} skipped`);
      if (result.deleted) parts.push(`${result.deleted} deleted first`);
      notify(`Import finished: ${parts.join(", ")}.`);
      await load();
    } catch (error) {
      const box = $("import-error");
      const errors = error && error.data && error.data.errors;
      box.replaceChildren(
        el("div", { class: "fw-semibold mb-1", text: errors ? "Nothing was imported. Fix these problems and try again:" : errorMessage(error) }),
        errors ? el("ul", { class: "mb-0 small" }, errors.map((text) => el("li", { text }))) : null
      );
      box.classList.remove("d-none");
    } finally {
      $("import-submit").disabled = false;
    }
  });

  load();
})();
