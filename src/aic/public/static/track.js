// Best-effort event beacon. Never blocks or throws visibly — if this fails
// (ad blocker, network hiccup), the page and every core action still work.
(function () {
  function track(eventType) {
    try {
      fetch("/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event_type: eventType }),
        keepalive: true,
      }).catch(function () {});
    } catch (err) {
      // intentionally swallowed
    }
  }

  // The landing page is pre-rendered static HTML in production (S3/CloudFront
  // — research.md Decision 7), so the server-side `landing_visit` recording
  // `GET /` performs never runs per real visitor there. Locally (`uvicorn`),
  // that server-side recording is still the mechanism of record, so this
  // beacon must not also fire there or visits would be double-counted — the
  // hostname is the only environment signal available to a shared static
  // file with no build step (research.md Decision 9).
  function isLocalDev() {
    return /^(localhost|127\.0\.0\.1|\[::1\])$/.test(window.location.hostname);
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (
      (window.location.pathname === "/" || window.location.pathname === "/index.html") &&
      !isLocalDev()
    ) {
      track("landing_visit");
    }

    var seenDemo = false;
    document.querySelectorAll("[data-track]").forEach(function (el) {
      el.addEventListener("click", function () {
        var eventType = el.getAttribute("data-track");
        if (eventType === "demo_interaction" && seenDemo) {
          return;
        }
        if (eventType === "demo_view") {
          seenDemo = true;
        }
        track(eventType);
      });
    });
  });
})();
