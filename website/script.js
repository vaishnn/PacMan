/**
 * script.js
 * This script adds interactivity to the PacMan website.
 * It includes a "fade-in on scroll" animation for sections.
 */

document.addEventListener("DOMContentLoaded", function () {
  // --- Smooth Scroll for Navigation Links ---
  // This part is handled by the CSS `scroll-behavior: smooth;` but could be extended here if needed.

  // --- Fade-in Animation on Scroll ---
  const sections = document.querySelectorAll("section");

  // Options for the Intersection Observer
  const options = {
    root: null, // it is the viewport
    threshold: 0.1, // 10% of the item is visible
    rootMargin: "0px",
  };

  // The observer that will watch for sections entering the viewport
  const observer = new IntersectionObserver(function (entries, observer) {
    entries.forEach((entry) => {
      // If the section is intersecting (visible)
      if (entry.isIntersecting) {
        // Add a class to make it visible
        entry.target.classList.add("is-visible");
        // Stop observing the element once it's visible
        observer.unobserve(entry.target);
      }
    });
  }, options);

  // Add the 'fade-in-section' class to all sections and observe them
  sections.forEach((section) => {
    section.classList.add("fade-in-section");
    observer.observe(section);
  });
});
