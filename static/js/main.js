(() => {
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".site-nav");

  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
    });

    nav.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  document.documentElement.classList.add("js-ready");

  document.querySelectorAll(".video-lazy").forEach((box) => {
    box.addEventListener(
      "click",
      () => {
        if (box.classList.contains("is-playing")) return;
        const src = box.getAttribute("data-src");
        if (!src) return;
        const poster = box.getAttribute("data-poster") || "";
        const video = document.createElement("video");
        video.controls = true;
        video.playsInline = true;
        video.preload = "auto";
        if (poster) video.poster = poster;
        const source = document.createElement("source");
        source.src = src;
        if (src.toLowerCase().includes(".mp4")) source.type = "video/mp4";
        video.appendChild(source);
        box.classList.add("is-playing");
        box.replaceChildren(video);
        video.play().catch(() => {});
      },
      { once: true }
    );
  });

  const revealEls = document.querySelectorAll(".js-reveal, .page-hero, main > .section");
  if (!revealEls.length) return;

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    revealEls.forEach((el) => el.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
  );

  revealEls.forEach((el, index) => {
    el.style.setProperty("--reveal-delay", `${Math.min(index * 0.04, 0.28)}s`);
    observer.observe(el);
  });
})();
