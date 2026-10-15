/**
 * Pitch Slides Deck UI: Interactive pitch deck presentation for judges
 */

export function initSlidesUI(slides) {
  let currentSlide = 0;
  const contentArea = document.getElementById("slide-content");
  const indicator = document.getElementById("slide-indicator");
  const dotsContainer = document.getElementById("slide-dots-container");
  const btnPrev = document.getElementById("btn-prev-slide");
  const btnNext = document.getElementById("btn-next-slide");

  if (!slides || slides.length === 0) return;

  function renderSlide(index) {
    currentSlide = index;
    const s = slides[currentSlide];

    indicator.innerText = `SLIDE ${currentSlide + 1} OF ${slides.length}`;
    contentArea.innerHTML = `
      <h2>${s.title}</h2>
      <h4>${s.subtitle}</h4>
      <ul class="slide-bullets">
        ${s.bulletPoints.map(b => `<li>${b}</li>`).join("")}
      </ul>
    `;

    // Render dots
    dotsContainer.innerHTML = "";
    slides.forEach((_, i) => {
      const dot = document.createElement("div");
      dot.className = `slide-dot ${i === currentSlide ? "active" : ""}`;
      dot.addEventListener("click", () => renderSlide(i));
      dotsContainer.appendChild(dot);
    });

    btnPrev.disabled = currentSlide === 0;
    btnNext.disabled = currentSlide === slides.length - 1;
  }

  btnPrev.onclick = () => {
    if (currentSlide > 0) renderSlide(currentSlide - 1);
  };

  btnNext.onclick = () => {
    if (currentSlide < slides.length - 1) renderSlide(currentSlide + 1);
  };

  // Keyboard navigation for arrow keys
  window.addEventListener("keydown", (e) => {
    const slidesTabActive = document.getElementById("pane-slides").classList.contains("active");
    if (!slidesTabActive) return;
    if (e.key === "ArrowRight" && currentSlide < slides.length - 1) {
      renderSlide(currentSlide + 1);
    } else if (e.key === "ArrowLeft" && currentSlide > 0) {
      renderSlide(currentSlide - 1);
    }
  });

  renderSlide(0);
}
