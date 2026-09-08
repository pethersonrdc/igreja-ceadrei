(() => {
  const strips = Array.from(document.querySelectorAll("[data-film-strip]"));
  if (!strips.length) return;

  strips.forEach((strip) => {
    const track = strip.querySelector(".film-strip-track");
    if (!track) return;

    function frames() {
      return Array.from(track.querySelectorAll(".film-strip-frame"));
    }

    if (frames().length < 2) return;

    const interval = Number(strip.dataset.filmInterval) || 3200;
    let timer = null;
    let dragging = false;
    let startX = 0;
    let startScroll = 0;
    let moved = false;

    function frameStep() {
      const first = frames()[0];
      if (!first) return 220;
      const style = window.getComputedStyle(track);
      const gap = Number.parseFloat(style.columnGap || style.gap || "8") || 8;
      return first.getBoundingClientRect().width + gap;
    }

    function scrollByFrames(dir) {
      const max = track.scrollWidth - track.clientWidth - 4;
      if (dir > 0 && track.scrollLeft >= max) {
        track.scrollTo({ left: 0, behavior: "smooth" });
        return;
      }
      if (dir < 0 && track.scrollLeft <= 4) {
        track.scrollTo({ left: Math.max(0, max), behavior: "smooth" });
        return;
      }
      track.scrollBy({ left: dir * frameStep(), behavior: "smooth" });
    }

    function stop() {
      if (timer) window.clearInterval(timer);
      timer = null;
    }

    function start() {
      stop();
      if (frames().length < 2) return;
      timer = window.setInterval(() => {
        if (dragging) return;
        scrollByFrames(1);
      }, interval);
    }

    track.addEventListener("click", (event) => {
      if (track.dataset.skipClick === "1") return;
      if (event.target.closest("video, a, button")) return;
      if (!event.target.closest(".film-strip-frame")) return;
      scrollByFrames(1);
      start();
    });

    track.addEventListener("pointerdown", (event) => {
      if (event.target.closest("video")) return;
      dragging = true;
      moved = false;
      startX = event.clientX;
      startScroll = track.scrollLeft;
      track.setPointerCapture?.(event.pointerId);
      track.classList.add("is-dragging");
      stop();
    });

    track.addEventListener("pointermove", (event) => {
      if (!dragging) return;
      const dx = event.clientX - startX;
      if (Math.abs(dx) > 4) moved = true;
      track.scrollLeft = startScroll - dx;
    });

    function endDrag() {
      if (!dragging) return;
      dragging = false;
      track.classList.remove("is-dragging");
      if (moved) {
        track.dataset.skipClick = "1";
        window.setTimeout(() => {
          delete track.dataset.skipClick;
        }, 80);
      }
      start();
    }

    track.addEventListener("pointerup", endDrag);
    track.addEventListener("pointercancel", endDrag);

    track.addEventListener(
      "click",
      (event) => {
        if (track.dataset.skipClick === "1") {
          event.stopPropagation();
          event.preventDefault();
        }
      },
      true
    );

    strip.addEventListener("mouseenter", stop);
    strip.addEventListener("mouseleave", start);
    track.addEventListener("touchstart", stop, { passive: true });
    track.addEventListener(
      "touchend",
      () => {
        window.setTimeout(start, 1200);
      },
      { passive: true }
    );

    start();
  });
})();
