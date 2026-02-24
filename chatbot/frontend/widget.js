(function() {
  'use strict';

  // Configuration - read from script tag attributes
  const currentScript = document.currentScript;
  const WIDGET_ID = 'ebottles-intake-widget';
  const BACKEND_URL = currentScript?.getAttribute('data-backend-url') || 'http://localhost:8080';
  const CALENDLY_URL = currentScript?.getAttribute('data-calendly-url') || 'https://calendly.com/ebottles';
  const API_KEY = currentScript?.getAttribute('data-api-key') || '';

  // Prevent multiple initializations
  if (document.getElementById(WIDGET_ID)) {
    console.warn('eBottles widget already initialized');
    return;
  }

  // eBottles brand colors (from their actual site)
  // Note: avoid external font loads inside embeds; rely on system font stack.
  const styles = `
    #${WIDGET_ID} {
      --eb-teal: #0d7377;
      --eb-teal-dark: #0a5c5f;
      --eb-teal-light: #e8f4f4;
      --eb-navy: #1a4f5c;
      --eb-mint: #7ecec8;
      --eb-text: #1a1a2e;
      --eb-text-light: #5a6a72;
      --eb-bg: #ffffff;
      --eb-bg-alt: #f5f9f9;
      --eb-border: #d4e5e5;
      --eb-error: #dc2626;
      --eb-success: #0d7377;
      --eb-shadow: 0 20px 60px rgba(13, 115, 119, 0.2);
      --eb-radius: 12px;
      --eb-radius-sm: 8px;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    .eb-widget-button {
      position: fixed;
      bottom: 24px;
      right: 24px;
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 14px 20px;
      background: linear-gradient(135deg, var(--eb-teal) 0%, var(--eb-navy) 100%);
      color: white;
      border: none;
      border-radius: 50px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      font-family: inherit;
      box-shadow: 0 8px 32px rgba(13, 115, 119, 0.4);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      z-index: 999999;
    }

    .eb-widget-button:hover {
      transform: translateY(-3px);
      box-shadow: 0 12px 40px rgba(13, 115, 119, 0.5);
    }

    .eb-widget-button:active {
      transform: translateY(-1px);
    }

    .eb-widget-button svg {
      width: 22px;
      height: 22px;
      flex-shrink: 0;
    }

    .eb-widget-button-text {
      white-space: nowrap;
    }

    @media (max-width: 500px) {
      .eb-widget-button {
        padding: 14px;
        border-radius: 50%;
      }
      .eb-widget-button-text {
        display: none;
      }
    }

    .eb-modal-overlay {
      position: fixed;
      inset: 0;
      background: rgba(26, 79, 92, 0.6);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
      z-index: 9999999;
      opacity: 0;
      visibility: hidden;
      transition: all 0.3s ease;
    }

    .eb-modal-overlay.eb-visible {
      opacity: 1;
      visibility: visible;
    }

    .eb-modal {
      background: var(--eb-bg);
      border-radius: var(--eb-radius);
      box-shadow: var(--eb-shadow);
      width: 100%;
      max-width: 480px;
      max-height: 90vh;
      overflow-y: auto;
      transform: translateY(20px) scale(0.95);
      transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* Mobile: fit above the fold by tightening spacing and using a full-height sheet */
    @media (max-width: 480px) {
      .eb-modal-overlay {
        padding: 0;
      }

      .eb-modal {
        max-width: 100%;
        width: 100%;
        height: 100vh;
        max-height: 100vh;
        border-radius: 0;
        display: flex;
        flex-direction: column;
      }

      .eb-modal-header {
        padding: 16px 16px 14px;
      }

      .eb-modal-title {
        font-size: 18px;
      }

      .eb-modal-subtitle {
        font-size: 12.5px;
      }

      .eb-modal-body {
        padding: 14px 16px;
        overflow: auto;
        flex: 1;
      }

      .eb-form-group {
        margin-bottom: 12px;
      }

      .eb-textarea {
        min-height: 74px;
        padding: 10px;
        font-size: 13.5px;
      }

      .eb-input,
      .eb-select {
        padding: 9px 10px;
        font-size: 13.5px;
      }

      .eb-char-count {
        margin-top: 2px;
      }

      .eb-divider {
        margin: 12px 0;
        font-size: 10px;
      }

      .eb-voice-button {
        padding: 8px 12px;
        margin-top: 6px;
      }

      .eb-modal-footer {
        padding: 12px 16px 14px;
        border-top: 1px solid var(--eb-border);
        background: var(--eb-bg);
        position: sticky;
        bottom: 0;
      }

      .eb-btn-primary {
        padding: 13px 18px;
      }
    }

    .eb-modal-overlay.eb-visible .eb-modal {
      transform: translateY(0) scale(1);
    }

    .eb-modal-header {
      background: linear-gradient(135deg, var(--eb-teal) 0%, var(--eb-navy) 100%);
      padding: 24px;
      position: relative;
      border-radius: var(--eb-radius) var(--eb-radius) 0 0;
    }

    .eb-modal-close {
      position: absolute;
      top: 16px;
      right: 16px;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(255, 255, 255, 0.15);
      border: none;
      border-radius: 50%;
      cursor: pointer;
      color: white;
      transition: all 0.2s;
    }

    .eb-modal-close:hover {
      background: rgba(255, 255, 255, 0.25);
    }

    .eb-modal-close svg {
      width: 16px;
      height: 16px;
    }

    .eb-modal-title {
      font-size: 20px;
      font-weight: 700;
      color: white;
      margin: 0 0 6px;
    }

    .eb-modal-subtitle {
      font-size: 14px;
      color: rgba(255, 255, 255, 0.85);
      margin: 0;
      line-height: 1.5;
    }

    .eb-modal-body {
      padding: 24px;
    }

    .eb-form-group {
      margin-bottom: 18px;
    }

    .eb-form-label {
      display: block;
      font-size: 13px;
      font-weight: 600;
      color: var(--eb-text);
      margin-bottom: 6px;
    }

    .eb-form-label .eb-required {
      color: var(--eb-error);
      margin-left: 2px;
    }

    .eb-textarea {
      width: 100%;
      min-height: 100px;
      padding: 12px;
      border: 2px solid var(--eb-border);
      border-radius: var(--eb-radius-sm);
      font-size: 14px;
      font-family: inherit;
      resize: vertical;
      transition: border-color 0.2s, box-shadow 0.2s;
      box-sizing: border-box;
    }

    .eb-textarea:focus {
      outline: none;
      border-color: var(--eb-teal);
      box-shadow: 0 0 0 3px var(--eb-teal-light);
    }

    .eb-textarea::placeholder {
      color: var(--eb-text-light);
    }

    .eb-input {
      width: 100%;
      padding: 10px 12px;
      border: 2px solid var(--eb-border);
      border-radius: var(--eb-radius-sm);
      font-size: 14px;
      font-family: inherit;
      transition: border-color 0.2s, box-shadow 0.2s;
      box-sizing: border-box;
    }

    .eb-input:focus {
      outline: none;
      border-color: var(--eb-teal);
      box-shadow: 0 0 0 3px var(--eb-teal-light);
    }

    .eb-select {
      width: 100%;
      padding: 10px 12px;
      border: 2px solid var(--eb-border);
      border-radius: var(--eb-radius-sm);
      font-size: 14px;
      font-family: inherit;
      background: white;
      cursor: pointer;
      transition: border-color 0.2s, box-shadow 0.2s;
      box-sizing: border-box;
    }

    .eb-select:focus {
      outline: none;
      border-color: var(--eb-teal);
      box-shadow: 0 0 0 3px var(--eb-teal-light);
    }

    .eb-input-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    @media (max-width: 480px) {
      .eb-input-row {
        grid-template-columns: 1fr;
      }
    }

    .eb-voice-button {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 14px;
      background: var(--eb-teal-light);
      border: 2px solid transparent;
      border-radius: var(--eb-radius-sm);
      font-size: 13px;
      font-weight: 500;
      font-family: inherit;
      color: var(--eb-teal);
      cursor: pointer;
      transition: all 0.2s;
      margin-top: 8px;
    }

    .eb-voice-button:hover {
      background: var(--eb-teal);
      color: white;
    }

    .eb-voice-button.eb-recording {
      background: #fee2e2;
      border-color: var(--eb-error);
      color: var(--eb-error);
      animation: eb-pulse 1.5s infinite;
    }

    @keyframes eb-pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.6; }
    }

    .eb-voice-button svg {
      width: 16px;
      height: 16px;
    }

    .eb-char-count {
      font-size: 11px;
      color: var(--eb-text-light);
      text-align: right;
      margin-top: 4px;
    }

    .eb-char-count.eb-error {
      color: var(--eb-error);
    }

    .eb-modal-footer {
      padding: 0 24px 24px;
      display: flex;
      gap: 12px;
      flex-direction: column;
    }

    .eb-btn-primary {
      width: 100%;
      padding: 14px 24px;
      background: linear-gradient(135deg, var(--eb-teal) 0%, var(--eb-navy) 100%);
      color: white;
      border: none;
      border-radius: var(--eb-radius-sm);
      font-size: 15px;
      font-weight: 600;
      font-family: inherit;
      cursor: pointer;
      transition: all 0.2s;
    }

    .eb-btn-primary:hover:not(:disabled) {
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(13, 115, 119, 0.4);
    }

    .eb-btn-primary:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .eb-btn-secondary {
      width: 100%;
      padding: 10px 24px;
      background: transparent;
      color: var(--eb-text-light);
      border: none;
      border-radius: var(--eb-radius-sm);
      font-size: 14px;
      font-weight: 500;
      font-family: inherit;
      cursor: pointer;
      transition: color 0.2s;
    }

    .eb-btn-secondary:hover {
      color: var(--eb-text);
    }

    .eb-form-error {
      background: #fef2f2;
      border: 1px solid #fecaca;
      color: var(--eb-error);
      padding: 12px 14px;
      border-radius: var(--eb-radius-sm);
      font-size: 13px;
      margin-bottom: 16px;
    }

    /* Success state */
    .eb-success-state {
      text-align: center;
      padding: 32px 24px;
    }

    .eb-success-icon {
      width: 64px;
      height: 64px;
      background: var(--eb-teal-light);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 20px;
    }

    .eb-success-icon svg {
      width: 32px;
      height: 32px;
      color: var(--eb-teal);
    }

    .eb-success-title {
      font-size: 18px;
      font-weight: 700;
      color: var(--eb-text);
      margin: 0 0 10px;
    }

    .eb-success-message {
      font-size: 14px;
      color: var(--eb-text-light);
      margin: 0 0 24px;
      line-height: 1.6;
    }

    .eb-success-link {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 12px 24px;
      background: var(--eb-teal);
      color: white;
      text-decoration: none;
      border-radius: var(--eb-radius-sm);
      font-size: 14px;
      font-weight: 600;
      transition: all 0.2s;
    }

    .eb-success-link:hover {
      background: var(--eb-navy);
      transform: translateY(-1px);
    }

    .eb-success-link svg {
      width: 18px;
      height: 18px;
    }

    /* Loading spinner */
    .eb-spinner {
      width: 18px;
      height: 18px;
      border: 2px solid transparent;
      border-top-color: currentColor;
      border-radius: 50%;
      animation: eb-spin 0.8s linear infinite;
      display: inline-block;
      margin-right: 8px;
      vertical-align: middle;
    }

    @keyframes eb-spin {
      to { transform: rotate(360deg); }
    }

    /* Section divider */
    .eb-divider {
      display: flex;
      align-items: center;
      gap: 12px;
      margin: 20px 0;
      color: var(--eb-text-light);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-weight: 600;
    }

    .eb-divider::before,
    .eb-divider::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--eb-border);
    }
  `;

  const styleSheet = document.createElement('style');
  styleSheet.textContent = styles;
  document.head.appendChild(styleSheet);

  // Create widget container
  const container = document.createElement('div');
  container.id = WIDGET_ID;

  // Chat/message icon (more friendly than robot)
  const chatIcon = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      <path d="M8 10h.01"/>
      <path d="M12 10h.01"/>
      <path d="M16 10h.01"/>
    </svg>
  `;

  // Microphone icon
  const micIcon = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
      <line x1="12" y1="19" x2="12" y2="23"/>
      <line x1="8" y1="23" x2="16" y2="23"/>
    </svg>
  `;

  // Close icon
  const closeIcon = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="18" y1="6" x2="6" y2="18"/>
      <line x1="6" y1="6" x2="18" y2="18"/>
    </svg>
  `;

  // Check icon
  const checkIcon = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  `;

  // Calendar icon
  const calendarIcon = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
      <line x1="16" y1="2" x2="16" y2="6"/>
      <line x1="8" y1="2" x2="8" y2="6"/>
      <line x1="3" y1="10" x2="21" y2="10"/>
    </svg>
  `;

  // State
  let isModalOpen = false;
  let isSubmitting = false;
  let isRecording = false;
  let mediaRecorder = null;
  let audioChunks = [];

  // Create floating button
  const button = document.createElement('button');
  button.className = 'eb-widget-button';
  button.setAttribute('aria-label', 'Talk to a packaging specialist');
  button.innerHTML = `${chatIcon}<span class="eb-widget-button-text">Talk to a Specialist</span>`;
  button.addEventListener('click', openModal);
  container.appendChild(button);

  // Create modal
  const modalOverlay = document.createElement('div');
  modalOverlay.className = 'eb-modal-overlay';
  modalOverlay.setAttribute('aria-hidden', 'true');
  modalOverlay.innerHTML = `
    <div class="eb-modal" role="dialog" aria-labelledby="eb-modal-title" aria-modal="true">
      <div class="eb-modal-header">
        <button class="eb-modal-close" aria-label="Close">${closeIcon}</button>
        <h2 class="eb-modal-title" id="eb-modal-title">Tell us what you need</h2>
        <p class="eb-modal-subtitle">Describe your packaging needs and we'll connect you with the right specialist (cannabis, nutraceutical, wellness, and CPG).</p>
      </div>
      <div class="eb-modal-body">
        <form id="eb-intake-form" novalidate>
          <div class="eb-form-error" id="eb-form-error" style="display: none;" role="alert"></div>
          
          <div class="eb-form-group">
            <label class="eb-form-label" for="eb-freeform">
              Describe your project <span class="eb-required">*</span>
            </label>
            <textarea 
              id="eb-freeform" 
              class="eb-textarea" 
              placeholder="Example: We need 5 oz child resistant jars for gummies in CA and MI, about 50k per month, ideally domestic stock and sustainable options."
              required
              minlength="40"
            ></textarea>
            <div class="eb-char-count" id="eb-char-count">0 / 40 minimum</div>
            <button type="button" class="eb-voice-button" id="eb-voice-btn">
              ${micIcon}
              <span>Speak instead</span>
            </button>
          </div>
          
          <div class="eb-divider">Your Contact Info</div>
          
          <div class="eb-form-group eb-input-row">
            <div>
              <label class="eb-form-label" for="eb-name">
                Full name <span class="eb-required">*</span>
              </label>
              <input type="text" id="eb-name" class="eb-input" required autocomplete="name" />
            </div>
            <div>
              <label class="eb-form-label" for="eb-company">
                Company <span class="eb-required">*</span>
              </label>
              <input type="text" id="eb-company" class="eb-input" required autocomplete="organization" />
            </div>
          </div>
          
          <div class="eb-form-group eb-input-row">
            <div>
              <label class="eb-form-label" for="eb-email">
                Work email <span class="eb-required">*</span>
              </label>
              <input type="email" id="eb-email" class="eb-input" required autocomplete="email" />
            </div>
            <div>
              <label class="eb-form-label" for="eb-phone">
                Phone <span style="color: #999; font-weight: 400;">(optional)</span>
              </label>
              <input type="tel" id="eb-phone" class="eb-input" autocomplete="tel" />
            </div>
          </div>
          
          <div class="eb-form-group">
            <label class="eb-form-label" for="eb-role">
              Which best describes you?
            </label>
            <select id="eb-role" class="eb-select">
              <option value="">Select one...</option>
              <option value="Brand or CPG company">Brand / CPG company</option>
              <option value="Nutraceutical or supplement brand">Nutraceutical / Supplement brand</option>
              <option value="Wellness, beauty, or personal care brand">Wellness / Beauty / Personal care</option>
              <option value="Manufacturer or co-packer">Manufacturer / Co-packer</option>
              <option value="Distributor or wholesaler">Distributor / Wholesaler</option>
              <option value="Retailer">Retailer</option>
              <option value="MSO or multi state operator">Cannabis: MSO / Multi-state operator</option>
              <option value="Single state operator">Cannabis: Single state operator</option>
              <option value="Other">Other</option>
            </select>
          </div>
        </form>
      </div>
      <div class="eb-modal-footer">
        <button type="submit" form="eb-intake-form" class="eb-btn-primary" id="eb-submit-btn">
          Send to Sales Team
        </button>
        <button type="button" class="eb-btn-secondary" id="eb-cancel-btn">
          Cancel
        </button>
      </div>
    </div>
  `;
  container.appendChild(modalOverlay);

  // Success state template
  const successTemplate = `
    <div class="eb-success-state">
      <div class="eb-success-icon">${checkIcon}</div>
      <h2 class="eb-success-title">Thank you!</h2>
      <p class="eb-success-message">
        We've received your project details. Our team will review and follow up within one business day.
      </p>
      <a href="${CALENDLY_URL}" target="_blank" rel="noopener noreferrer" class="eb-success-link">
        ${calendarIcon}
        Schedule a Call Now
      </a>
    </div>
  `;

  // Add to DOM
  document.body.appendChild(container);

  // Get elements
  const modal = modalOverlay.querySelector('.eb-modal');
  const closeBtn = modalOverlay.querySelector('.eb-modal-close');
  const cancelBtn = modalOverlay.querySelector('#eb-cancel-btn');
  const form = modalOverlay.querySelector('#eb-intake-form');
  const submitBtn = modalOverlay.querySelector('#eb-submit-btn');
  const freeformInput = modalOverlay.querySelector('#eb-freeform');
  const charCount = modalOverlay.querySelector('#eb-char-count');
  const voiceBtn = modalOverlay.querySelector('#eb-voice-btn');
  const formError = modalOverlay.querySelector('#eb-form-error');

  // Event handlers
  function openModal() {
    isModalOpen = true;
    modalOverlay.classList.add('eb-visible');
    modalOverlay.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    setTimeout(() => freeformInput.focus(), 100);
  }

  function closeModal() {
    isModalOpen = false;
    modalOverlay.classList.remove('eb-visible');
    modalOverlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    resetForm();
  }

  function resetForm() {
    form.reset();
    updateCharCount();
    formError.style.display = 'none';
    formError.textContent = '';
    submitBtn.disabled = false;
    submitBtn.innerHTML = 'Send to Sales Team';
    isSubmitting = false;
    stopRecording();
    
    // Reset modal content if showing success state
    const modalHeader = modalOverlay.querySelector('.eb-modal-header');
    const modalBody = modalOverlay.querySelector('.eb-modal-body');
    const modalFooter = modalOverlay.querySelector('.eb-modal-footer');
    if (modalHeader) modalHeader.style.display = '';
    if (modalFooter) modalFooter.style.display = '';
    
    const successState = modalBody.querySelector('.eb-success-state');
    if (successState) {
      successState.remove();
      form.style.display = '';
    }
  }

  function updateCharCount() {
    const length = freeformInput.value.length;
    charCount.textContent = `${length} / 40 minimum`;
    charCount.classList.toggle('eb-error', length > 0 && length < 40);
  }

  function showError(message) {
    formError.textContent = message;
    formError.style.display = 'block';
    formError.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function showSuccess() {
    const modalHeader = modalOverlay.querySelector('.eb-modal-header');
    const modalBody = modalOverlay.querySelector('.eb-modal-body');
    const modalFooter = modalOverlay.querySelector('.eb-modal-footer');
    
    modalHeader.style.display = 'none';
    modalFooter.style.display = 'none';
    form.style.display = 'none';
    modalBody.insertAdjacentHTML('beforeend', successTemplate);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    
    if (isSubmitting) return;
    
    const freeform = freeformInput.value.trim();
    const name = form.querySelector('#eb-name').value.trim();
    const company = form.querySelector('#eb-company').value.trim();
    const email = form.querySelector('#eb-email').value.trim();
    const phone = form.querySelector('#eb-phone').value.trim();
    const role = form.querySelector('#eb-role').value;
    
    // Validation
    if (freeform.length < 40) {
      showError('Please provide more detail about your packaging needs (at least 40 characters).');
      freeformInput.focus();
      return;
    }
    
    if (!name || !company || !email) {
      showError('Please fill in all required fields.');
      return;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      showError('Please enter a valid email address.');
      return;
    }
    
    isSubmitting = true;
    formError.style.display = 'none';
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="eb-spinner"></span>Sending...';
    
    const payload = {
      freeform_note: freeform,
      contact: {
        name,
        company,
        email,
        phone: phone || null,
      },
      role: role || null,
      metadata: {
        source: 'widget',
        user_agent: navigator.userAgent,
        page_url: window.location.href,
      },
    };
    
    try {
      const headers = {
        'Content-Type': 'application/json',
      };
      if (API_KEY) headers['X-API-KEY'] = API_KEY;

      const response = await fetch(`${BACKEND_URL}/lead-intake`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Something went wrong. Please try again.');
      }
      
      showSuccess();
      
    } catch (error) {
      console.error('Lead intake error:', error);
      // Browser may throw TypeError("Failed to fetch") for CORS/network.
      const msg = (error && error.message) ? error.message : '';
      if (msg.toLowerCase().includes('failed to fetch')) {
        showError('Unable to reach the intake service. If this is a demo link, refresh and try again. If it persists, the site may need CORS enabled for this domain.');
      } else {
        showError(msg || 'Unable to submit. Please try again or contact us directly.');
      }
      submitBtn.disabled = false;
      submitBtn.innerHTML = 'Send to Sales Team';
      isSubmitting = false;
    }
  }

  // Voice recording
  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Check for supported mime types
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') 
        ? 'audio/webm' 
        : (MediaRecorder.isTypeSupported('audio/mp4') ? 'audio/mp4' : '');
      
      mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      audioChunks = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunks.push(e.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(track => track.stop());
        const blobType = mimeType || (audioChunks[0] && audioChunks[0].type) || 'audio/webm';
        const audioBlob = new Blob(audioChunks, { type: blobType });
        await transcribeAudio(audioBlob, blobType);
      };
      
      mediaRecorder.start();
      isRecording = true;
      voiceBtn.classList.add('eb-recording');
      voiceBtn.querySelector('span').textContent = 'Recording... tap to stop';
      
    } catch (error) {
      console.error('Microphone access error:', error);
      showError('Unable to access microphone. Please check your browser permissions.');
    }
  }

  function stopRecording() {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      isRecording = false;
      voiceBtn.classList.remove('eb-recording');
      voiceBtn.querySelector('span').textContent = 'Speak instead';
    }
  }

  function extForMime(mime) {
    if (!mime) return 'webm';
    if (mime.includes('webm')) return 'webm';
    if (mime.includes('mp4')) return 'mp4';
    if (mime.includes('mpeg') || mime.includes('mp3')) return 'mp3';
    if (mime.includes('wav')) return 'wav';
    if (mime.includes('ogg')) return 'ogg';
    return 'webm';
  }

  async function transcribeAudio(audioBlob, mimeType) {
    voiceBtn.disabled = true;
    voiceBtn.querySelector('span').textContent = 'Transcribing...';
    
    try {
      const formData = new FormData();
      const filename = `recording.${extForMime(mimeType || audioBlob.type)}`;
      formData.append('audio', audioBlob, filename);

      const headers = {};
      if (API_KEY) headers['X-API-KEY'] = API_KEY;
      
      const response = await fetch(`${BACKEND_URL}/transcribe`, {
        method: 'POST',
        headers,
        body: formData,
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Transcription failed');
      }
      
      if (data.text) {
        const existing = freeformInput.value.trim();
        freeformInput.value = existing ? `${existing} ${data.text}` : data.text;
        updateCharCount();
        freeformInput.focus();
      }
      
    } catch (error) {
      console.error('Transcription error:', error);
      showError('Unable to transcribe audio. Please try typing instead.');
    } finally {
      voiceBtn.disabled = false;
      voiceBtn.querySelector('span').textContent = 'Speak instead';
    }
  }

  function handleVoiceClick() {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }

  // Event listeners
  closeBtn.addEventListener('click', closeModal);
  cancelBtn.addEventListener('click', closeModal);
  form.addEventListener('submit', handleSubmit);
  freeformInput.addEventListener('input', updateCharCount);
  voiceBtn.addEventListener('click', handleVoiceClick);

  // Close on overlay click
  modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) {
      closeModal();
    }
  });

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isModalOpen) {
      closeModal();
    }
  });

  // Prevent modal from closing on modal click
  modal.addEventListener('click', (e) => {
    e.stopPropagation();
  });

  // Log initialization (only in dev)
  if (BACKEND_URL.includes('localhost')) {
    console.log('eBottles AI Intake Widget initialized (dev mode)');
  }
})();
