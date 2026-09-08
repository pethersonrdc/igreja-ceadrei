(() => {
  const roots = Array.from(document.querySelectorAll("[data-carousel]"));
  if (!roots.length) return;

  const PLACEHOLDER =
    "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==";

  roots.forEach((root) => {
    const slides = Array.from(root.querySelectorAll(".carousel-slide"));
    const prevBtn = root.querySelector("[data-carousel-prev]");
    const nextBtn = root.querySelector("[data-carousel-next]");
    const dotsWrap = root.querySelector("[data-carousel-dots]");
    const counter = root.querySelector("[data-carousel-counter]");
    if (slides.length < 2) return;

    const manual =
      root.hasAttribute("data-carousel-manual") ||
      root.dataset.carouselInterval === "0";
    const interval = Number(root.dataset.carouselInterval) || 4500;
    let index = 0;
    let timer = null;

    const dots = slides.map((_, i) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "carousel-dot";
      btn.setAttribute("aria-label", `Ir para foto ${i + 1}`);
      btn.addEventListener("click", (event) => {
        event.stopPropagation();
        goTo(i);
        if (!manual) start();
      });
      dotsWrap?.appendChild(btn);
      return btn;
    });

    function hydrateSlide(i) {
      const slide = slides[(i + slides.length) % slides.length];
      if (!slide) return;
      slide.querySelectorAll("img[data-src]").forEach((img) => {
        const src = img.getAttribute("data-src");
        if (!src) return;
        img.setAttribute("src", src);
        img.removeAttribute("data-src");
        const srcset = img.getAttribute("data-srcset");
        if (srcset) {
          img.setAttribute("srcset", srcset);
          img.removeAttribute("data-srcset");
        }
      });
    }

    function hydrateAround(i) {
      hydrateSlide(i);
      hydrateSlide(i - 1);
      hydrateSlide(i + 1);
    }

    function updateCounter() {
      if (counter) {
        counter.textContent = `${index + 1} / ${slides.length}`;
      }
    }

    function goTo(next) {
      slides[index].classList.remove("is-active");
      dots[index]?.classList.remove("is-active");
      index = (next + slides.length) % slides.length;
      slides[index].classList.add("is-active");
      dots[index]?.classList.add("is-active");
      hydrateAround(index);
      updateCounter();
    }

    function start() {
      if (manual) return;
      stop();
      timer = window.setInterval(() => goTo(index + 1), interval);
    }

    function stop() {
      if (timer) window.clearInterval(timer);
      timer = null;
    }

    prevBtn?.addEventListener("click", (event) => {
      event.stopPropagation();
      goTo(index - 1);
      if (!manual) start();
    });
    nextBtn?.addEventListener("click", (event) => {
      event.stopPropagation();
      goTo(index + 1);
      if (!manual) start();
    });

    // Avança ao clicar na foto (modo manual ou também no automático)
    root.addEventListener("click", (event) => {
      if (event.target.closest("button, a, video, .carousel-dot")) return;
      if (!event.target.closest(".carousel-slide, .carousel-track")) return;
      goTo(index + 1);
      if (!manual) start();
    });

    if (!manual) {
      root.addEventListener("mouseenter", stop);
      root.addEventListener("mouseleave", start);
    }

    // Slides sem data-src já têm src; garante placeholder só onde falta
    slides.forEach((slide) => {
      slide.querySelectorAll("img[data-src]").forEach((img) => {
        if (!img.getAttribute("src")) {
          img.setAttribute("src", PLACEHOLDER);
        }
      });
    });

    dots[0]?.classList.add("is-active");
    hydrateAround(0);
    updateCounter();
    start();
  });
})();
