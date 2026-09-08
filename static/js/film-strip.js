(() => {
  const strips = Array.from(document.querySelectorAll("[data-film-strip]"));
  if (!strips.length) return;

  strips.forEach((strip) => {
    const track = strip.querySelector(".film-strip-track");
    if (!track) return;

    const frames = () => Array.from(track.querySelectorAll(".film-strip-frame"));

    function frameStep() {
      const first = frames()[0];
      if (!first) return 220;
      const style = window.getComputedStyle(track);
      const gap = Number.parseFloat(style.columnGap || style.gap || "8") || 8;
      return first.getBoundingClientRect().width + gap;
    }

    function scrollByFrames(dir) {
      track.scrollBy({ left: dir * frameStep(), behavior: "smooth" });
    }

    // Clique na foto (não no vídeo) avança um quadro
    track.addEventListener("click", (event) => {
      if (event.target.closest("video, a, button")) return;
      if (!event.target.closest(".film-strip-frame")) return;
      const max = track.scrollWidth - track.clientWidth - 4;
      if (track.scrollLeft >= max) {
        track.scrollTo({ left: 0, behavior: "smooth" });
      } else {
        scrollByFrames(1);
      }
    });

    // Arraste leve com mouse (além do scroll nativo no touch)
    let dragging = false;
    let startX = 0;
    let startScroll = 0;
    let moved = false;

    track.addEventListener("pointerdown", (event) => {
      if (event.target.closest("video")) return;
      dragging = true;
      moved = false;
      startX = event.clientX;
      startScroll = track.scrollLeft;
      track.setPointerCapture?.(event.pointerId);
      track.classList.add("is-dragging");
    });

    track.addEventListener("pointermove", (event) => {
      if (!dragging) return;
      const dx = event.clientX - startX;
      if (Math.abs(dx) > 4) moved = true;
      track.scrollLeft = startScroll - dx;
    });

    function endDrag(event) {
      if (!dragging) return;
      dragging = false;
      track.classList.remove("is-dragging");
      // Se foi arraste, evita o click de avanço
      if (moved) {
        event.preventDefault?.();
        track.dataset.skipClick = "1";
        window.setTimeout(() => {
          delete track.dataset.skipClick;
        }, 80);
      }
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
  });
})();
