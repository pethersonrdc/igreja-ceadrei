import Lightbox from "https://cdn.jsdelivr.net/npm/photoswipe@5.4.4/dist/photoswipe-lightbox.esm.min.js";
import PhotoSwipe from "https://cdn.jsdelivr.net/npm/photoswipe@5.4.4/dist/photoswipe.esm.min.js";

const galleries = document.querySelectorAll("[data-pswp-gallery]");
if (galleries.length) {
  galleries.forEach((gallery) => {
    const lightbox = new Lightbox({
      gallery,
      children: "a",
      pswpModule: PhotoSwipe,
      padding: { top: 20, bottom: 40, left: 20, right: 20 },
    });
    lightbox.init();
  });
}
