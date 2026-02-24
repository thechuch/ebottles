/**
 * landing.js — Split-screen interaction logic
 *
 * STATES (CSS classes on #splitScreen):
 *   (none)               → 50/50 default split
 *   .is-hover-cannabis   → Left panel expanded to 77%
 *   .is-hover-wellness   → Right panel expanded to 77%
 *   .is-clicked-cannabis → Left panel takes 100%, then navigate
 *   .is-clicked-wellness → Right panel takes 100%, then navigate
 *
 * SHOPIFY: This becomes assets/section-landing-split.js
 * Load it with: <script src="{{ 'section-landing-split.js' | asset_url }}" defer></script>
 */

(function () {
  'use strict';

  // ---- DOM References ----
  var splitScreen = document.getElementById('splitScreen');
  var panelCannabis = document.getElementById('panelCannabis');
  var panelWellness = document.getElementById('panelWellness');

  if (!splitScreen || !panelCannabis || !panelWellness) return;

  // ---- State ----
  var isClicked = false;
  var isMobile = window.matchMedia('(max-width: 768px)').matches;
  var hasHover = window.matchMedia('(hover: hover)').matches;

  // ---- Wellness Image Offset ----
  // On desktop, the wellness panel's image-wrapper must be pulled LEFT
  // by the cannabis panel's current width, so both images align to
  // the viewport's left edge (making the reveal illusion work).
  var wellnessImageWrapper = panelWellness.querySelector('.split-screen__image-wrapper');
  var rafId = null;

  function updateWellnessOffset() {
    if (isMobile || !wellnessImageWrapper) return;

    var cannabisWidth = panelCannabis.getBoundingClientRect().width;
    wellnessImageWrapper.style.left = '-' + cannabisWidth + 'px';
  }

  // Continuously update offset during transitions (requestAnimationFrame loop)
  function trackTransition() {
    updateWellnessOffset();
    rafId = requestAnimationFrame(trackTransition);
  }

  function startTracking() {
    if (rafId) cancelAnimationFrame(rafId);
    trackTransition();
  }

  function stopTracking() {
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    updateWellnessOffset();
  }


  // ---- Hover Handlers (desktop only) ----
  function onPanelEnter(side) {
    if (isClicked || isMobile || !hasHover) return;

    splitScreen.classList.remove('is-hover-cannabis', 'is-hover-wellness');
    splitScreen.classList.add('is-hover-' + side);
    startTracking();
  }

  function onPanelLeave() {
    if (isClicked || isMobile || !hasHover) return;

    splitScreen.classList.remove('is-hover-cannabis', 'is-hover-wellness');
    startTracking();
  }


  // ---- Click Handler ----
  function onPanelClick(side) {
    if (isClicked) return;
    isClicked = true;

    var panel = side === 'cannabis' ? panelCannabis : panelWellness;
    var targetUrl = panel.getAttribute('data-target');

    // Remove hover state, add click state
    splitScreen.classList.remove('is-hover-cannabis', 'is-hover-wellness');
    splitScreen.classList.add('is-clicked-' + side);
    startTracking();

    // Navigate after the CSS transition completes (800ms + 50ms buffer)
    // SHOPIFY: In production, use transitionend event instead of setTimeout
    setTimeout(function () {
      window.location.href = targetUrl;
    }, 850);
  }


  // ---- Event Binding ----
  panelCannabis.addEventListener('mouseenter', function () { onPanelEnter('cannabis'); });
  panelCannabis.addEventListener('mouseleave', onPanelLeave);
  panelCannabis.addEventListener('click', function () { onPanelClick('cannabis'); });

  panelWellness.addEventListener('mouseenter', function () { onPanelEnter('wellness'); });
  panelWellness.addEventListener('mouseleave', onPanelLeave);
  panelWellness.addEventListener('click', function () { onPanelClick('wellness'); });

  // Stop rAF loop when transition finishes
  splitScreen.addEventListener('transitionend', function (e) {
    if (e.propertyName === 'flex-basis') {
      stopTracking();
    }
  });


  // ---- Responsive: detect breakpoint changes ----
  var mqMobile = window.matchMedia('(max-width: 768px)');
  mqMobile.addEventListener('change', function (e) {
    isMobile = e.matches;
    if (isMobile) {
      splitScreen.classList.remove('is-hover-cannabis', 'is-hover-wellness');
      if (wellnessImageWrapper) wellnessImageWrapper.style.left = '0';
    } else {
      updateWellnessOffset();
    }
  });

  var mqHover = window.matchMedia('(hover: hover)');
  mqHover.addEventListener('change', function (e) {
    hasHover = e.matches;
  });


  // ---- Initial setup ----
  updateWellnessOffset();
  window.addEventListener('resize', updateWellnessOffset);

})();
