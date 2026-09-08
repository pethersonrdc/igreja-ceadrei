(() => {
  const roots = Array.from(document.querySelectorAll("[data-spotlight]"));
  if (!roots.length) return;

  roots.forEach((root) => {
    const main = root.querySelector("[data-spotlight-main]");
    const caption = root.querySelector("[data-spotlight-caption]");
    const thumbs = Array.from(root.querySelectorAll("[data-spotlight-thumb]"));
    if (!main || thumbs.length < 2) return;

    const interval = Number(root.dataset.spotlightInterval) || 3500;
    let index = 0;
    let timer = null;

    function goTo(next) {
      index = (next + thumbs.length) % thumbs.length;
      const thumb = thumbs[index];
      main.src = thumb.dataset.src || main.src;
      main.alt = thumb.dataset.titulo || "";
      if (caption) {
        const strong = caption.querySelector("strong");
        const span = caption.querySelector("span");
        if (strong) strong.textContent = thumb.dataset.titulo || "";
        if (span) {
          const data = thumb.dataset.data || "";
          span.textContent = data;
          span.hidden = !data;
        }
      }
      thumbs.forEach((btn, i) => {
        btn.classList.toggle("is-active", i === index);
      });
    }

    function stop() {
      if (timer) window.clearInterval(timer);
      timer = null;
    }

    function start() {
      stop();
      timer = window.setInterval(() => goTo(index + 1), interval);
    }

    thumbs.forEach((thumb, i) => {
      thumb.addEventListener("click", () => {
        goTo(i);
        start();
      });
    });

    root.addEventListener("mouseenter", stop);
    root.addEventListener("mouseleave", start);
    root.addEventListener("touchstart", stop, { passive: true });
    root.addEventListener(
      "touchend",
      () => {
        window.setTimeout(start, 1400);
      },
      { passive: true }
    );

    start();
  });
})();
