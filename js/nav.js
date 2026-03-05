/**
 * nav.js — Navigation overlay toggle
 *
 * Manages the pull-tab (desktop) and hamburger (mobile) triggers
 * that open a shared frosted-glass nav overlay.
 *
 * Exposes window.__ebNavOpen so landing.js can pause hover effects.
 *
 * SHOPIFY: Merge into assets/section-nav.js or theme.js
 */

(function () {
  'use strict';

  // ---- DOM References ----
  var navTab = document.getElementById('navTab');
  var navHamburger = document.getElementById('navHamburger');
  var navOverlay = document.getElementById('navOverlay');

  if (!navOverlay) return;

  // ---- State ----
  var isOpen = false;
  window.__ebNavOpen = false;

  // ---- Toggle ----
  function openNav() {
    isOpen = true;
    window.__ebNavOpen = true;

    if (navTab) {
      navTab.classList.add('is-open');
      navTab.setAttribute('aria-expanded', 'true');
    }
    if (navHamburger) {
      navHamburger.classList.add('is-open');
      navHamburger.setAttribute('aria-expanded', 'true');
    }

    navOverlay.classList.add('is-open');
    navOverlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    // Focus first link after transition
    setTimeout(function () {
      var firstLink = navOverlay.querySelector('.nav-overlay__link');
      if (firstLink) firstLink.focus();
    }, 350);
  }

  function closeNav() {
    isOpen = false;
    window.__ebNavOpen = false;

    if (navTab) {
      navTab.classList.remove('is-open');
      navTab.setAttribute('aria-expanded', 'false');
    }
    if (navHamburger) {
      navHamburger.classList.remove('is-open');
      navHamburger.setAttribute('aria-expanded', 'false');
    }

    navOverlay.classList.remove('is-open');
    navOverlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';

    // Return focus to the trigger that opened it
    var activeTrigger = window.matchMedia('(max-width: 768px)').matches
      ? navHamburger
      : navTab;
    if (activeTrigger) activeTrigger.focus();
  }

  function toggleNav() {
    if (isOpen) {
      closeNav();
    } else {
      openNav();
    }
  }

  // ---- Event Binding ----

  // Pull-tab trigger (desktop)
  if (navTab) {
    navTab.addEventListener('click', toggleNav);
  }

  // Hamburger trigger (mobile)
  if (navHamburger) {
    navHamburger.addEventListener('click', toggleNav);
  }

  // Escape key closes
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && isOpen) {
      closeNav();
    }
  });

  // Clicking a nav link closes + navigates
  navOverlay.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', function () {
      closeNav();
      // Let the default link navigation happen naturally
    });
  });

})();
