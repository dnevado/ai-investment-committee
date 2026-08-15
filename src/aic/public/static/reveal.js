// Very discreet scroll reveal. Progressive enhancement only: elements start
// fully visible in CSS, and this script opts them into a brief fade/settle
// only when it can actually observe and animate them — so a JS failure or
// missing IntersectionObserver never leaves content hidden.
(function () {
  if (
    typeof IntersectionObserver === "undefined" ||
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  ) {
    return;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var targets = document.querySelectorAll(".reveal");
    if (!targets.length) {
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.remove("reveal-pending");
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );

    targets.forEach(function (el) {
      el.classList.add("reveal-pending");
      observer.observe(el);
    });
  });
})();
