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

  document.addEventListener("DOMContentLoaded", function () {
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
