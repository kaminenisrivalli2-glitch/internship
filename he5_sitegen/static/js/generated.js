document.addEventListener("DOMContentLoaded", function () {
  // Scroll-triggered reveal animations
  if (window.AOS) {
    AOS.init({ duration: 700, once: true, offset: 80 });
  }

  // Footer year
  const yearEl = document.getElementById("he5Year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // Navbar shrink/shadow on scroll
  const navbar = document.getElementById("he5Navbar");
  if (navbar) {
    window.addEventListener("scroll", function () {
      navbar.classList.toggle("he5-scrolled", window.scrollY > 20);
    });
  }

  // Smooth scroll for in-page anchor links
  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener("click", function (e) {
      const targetId = this.getAttribute("href");
      if (targetId.length > 1) {
        const target = document.querySelector(targetId);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
    });
  });

  // Basic client-side contact form validation feedback
  const contactForm = document.querySelector(".he5-contact-form");
  if (contactForm) {
    contactForm.addEventListener("submit", function (e) {
      const inputs = contactForm.querySelectorAll("[required]");
      let valid = true;
      inputs.forEach((input) => {
        if (!input.value.trim()) {
          valid = false;
          input.classList.add("is-invalid");
        } else {
          input.classList.remove("is-invalid");
        }
      });
      if (!valid) e.preventDefault();
    });
  }
});
