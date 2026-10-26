// Launcher page: instant search over the tiles.
//   "/" focuses the search, Enter opens the first match, Escape clears.
(function () {
  const search = document.getElementById("search");
  if (!search) return;
  const tiles = Array.from(document.querySelectorAll("#tiles .tile"));
  const count = document.getElementById("count");
  const noResults = document.getElementById("no-results");

  function filter() {
    const words = search.value.toLowerCase().split(/\s+/).filter(Boolean);
    let visible = [];
    tiles.forEach((tile) => {
      const match = words.every((word) => tile.dataset.search.includes(word));
      tile.hidden = !match;
      tile.classList.remove("is-first-match");
      if (match) visible.push(tile);
    });
    if (words.length && visible.length) visible[0].classList.add("is-first-match");
    count.textContent = words.length ? `${visible.length} of ${tiles.length}` : tiles.length;
    noResults.classList.toggle("d-none", visible.length > 0);
    return visible;
  }

  search.addEventListener("input", filter);
  search.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      const first = filter()[0];
      if (first) window.open(first.href, "_blank", "noopener");
    } else if (event.key === "Escape") {
      search.value = "";
      filter();
      search.blur();
    }
  });

  document.addEventListener("keydown", (event) => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
    if (event.key === "/" && !typing && !event.ctrlKey && !event.metaKey) {
      event.preventDefault();
      search.focus();
    }
  });
})();
