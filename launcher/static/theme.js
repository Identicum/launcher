// Light / dark / auto theme. Loaded in <head> so the page never flashes the wrong theme.
(function () {
  const KEY = "launcher.theme";
  const ORDER = ["auto", "light", "dark"];
  const media = window.matchMedia("(prefers-color-scheme: dark)");

  function stored() {
    try {
      return ORDER.includes(localStorage.getItem(KEY)) ? localStorage.getItem(KEY) : "auto";
    } catch (e) {
      return "auto";
    }
  }

  function apply(choice) {
    const theme = choice === "auto" ? (media.matches ? "dark" : "light") : choice;
    document.documentElement.setAttribute("data-bs-theme", theme);
    document.querySelectorAll("[data-theme-label]").forEach((el) => (el.textContent = choice));
  }

  apply(stored());
  media.addEventListener("change", () => apply(stored()));

  document.addEventListener("DOMContentLoaded", () => {
    apply(stored());
    document.querySelectorAll("[data-theme-toggle]").forEach((button) =>
      button.addEventListener("click", (event) => {
        event.stopPropagation(); // keep the menu open to show the new choice
        const next = ORDER[(ORDER.indexOf(stored()) + 1) % ORDER.length];
        try {
          localStorage.setItem(KEY, next);
        } catch (e) {
          // storage blocked: the choice lasts until the page is reloaded
        }
        apply(next);
      })
    );
  });
})();
