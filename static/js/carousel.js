(() => {
  const root = document.querySelector("[data-carousel]");
  if (!root) return;

  const slides = Array.from(root.querySelectorAll(".carousel-slide"));
  const prevBtn = root.querySelector("[data-carousel-prev]");
  const nextBtn = root.querySelector("[data-carousel-next]");
  const dotsWrap = root.querySelector("[data-carousel-dots]");
  if (slides.length < 2) return;

  let index = 0;
  let timer = null;

  const dots = slides.map((_, i) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "carousel-dot";
    btn.setAttribute("aria-label", `Ir para foto ${i + 1}`);
    btn.addEventListener("click", () => goTo(i));
    dotsWrap?.appendChild(btn);
    return btn;
  });

  function goTo(next) {
    slides[index].classList.remove("is-active");
    dots[index]?.classList.remove("is-active");
    index = (next + slides.length) % slides.length;
    slides[index].classList.add("is-active");
    dots[index]?.classList.add("is-active");
  }

  function start() {
    stop();
    timer = window.setInterval(() => goTo(index + 1), 4500);
  }

  function stop() {
    if (timer) window.clearInterval(timer);
  }

  prevBtn?.addEventListener("click", () => {
    goTo(index - 1);
    start();
  });
  nextBtn?.addEventListener("click", () => {
    goTo(index + 1);
    start();
  });

  root.addEventListener("mouseenter", stop);
  root.addEventListener("mouseleave", start);

  dots[0]?.classList.add("is-active");
  start();
})();
