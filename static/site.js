'use strict';
(() => {
  const toast = document.getElementById('toast');
  let toastTimer;
  function notify(message) {
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.hidden = true; }, 4500);
  }
  const menu = document.querySelector('.menu-toggle');
  const nav = document.getElementById('site-nav');
  function closeMenu() { nav.classList.remove('is-open'); menu.setAttribute('aria-expanded', 'false'); menu.setAttribute('aria-label', 'Abrir menu'); }
  menu.addEventListener('click', () => {
    const open = nav.classList.toggle('is-open');
    menu.setAttribute('aria-expanded', String(open));
    menu.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
  });
  nav.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && nav.classList.contains('is-open')) { closeMenu(); menu.focus(); } });
  document.querySelectorAll('[data-copy]').forEach(button => {
    button.addEventListener('click', async () => {
      let copied = false;
      try { await navigator.clipboard.writeText(button.dataset.copy); copied = true; } catch (_) {
        const helper = document.createElement('textarea');
        helper.value = button.dataset.copy;
        helper.style.cssText = 'position:fixed;left:-9999px;top:0';
        document.body.append(helper);
        helper.select();
        try { copied = document.execCommand('copy'); } catch (_) { /* manual copy remains available */ }
        helper.remove();
        button.focus();
      }
      if (copied) notify('Chave PIX copiada! Confira o destinatário antes de pagar.');
      else { button.parentElement.querySelector('.copy-manual').hidden = false; notify('Selecione a chave PIX para copiar manualmente.'); }
    });
  });
  document.querySelectorAll('[data-print]').forEach(button => button.addEventListener('click', () => window.print()));
  const checklist = [...document.querySelectorAll('[data-pack]')];
  const count = document.getElementById('packed-count');
  function updateCount() { if (count) count.textContent = checklist.filter(input => input.checked).length; }
  checklist.forEach(input => {
    try { input.checked = localStorage.getItem(`shekinah-2027-pack-${input.dataset.pack}`) === 'true'; } catch (_) { /* list still works without storage */ }
    input.addEventListener('change', () => {
      try { localStorage.setItem(`shekinah-2027-pack-${input.dataset.pack}`, String(input.checked)); } catch (_) { /* optional persistence */ }
      updateCount();
    });
  });
  updateCount();
  const togglePassword = document.getElementById('toggle-password');
  if (togglePassword) togglePassword.addEventListener('click', () => {
    const password = document.getElementById('senha');
    const show = password.type === 'password';
    password.type = show ? 'text' : 'password';
    togglePassword.textContent = show ? 'Ocultar' : 'Mostrar';
    togglePassword.setAttribute('aria-pressed', String(show));
  });
  const form = document.getElementById('registration-form');
  if (!form) return;
  const steps = [...form.querySelectorAll('[data-step]')];
  const indicators = [...document.querySelectorAll('[data-step-indicator]')];
  const next = document.getElementById('step-next');
  const back = document.getElementById('step-back');
  const submit = document.getElementById('submit-registration');
  const type = document.getElementById('tipo');
  const arrival = document.getElementById('chegada');
  const payment = document.getElementById('pagamento');
  let current = 0;
  function syncArrival() {
    const worker = type.value === 'Trabalhador';
    document.getElementById('chegada-field').hidden = !worker;
    arrival.required = worker;
    arrival.disabled = !worker;
  }
  function syncPayment() {
    document.getElementById('pix-details').hidden = payment.value !== 'PIX';
    document.getElementById('cash-details').hidden = payment.value !== 'Dinheiro';
  }
  type.addEventListener('change', syncArrival);
  payment.addEventListener('change', syncPayment);
  syncArrival(); syncPayment();
  function showStep(index, focus = true) {
    current = index;
    steps.forEach((step, i) => { step.hidden = i !== index; });
    indicators.forEach((indicator, i) => {
      indicator.classList.toggle('active', i === index);
      indicator.classList.toggle('complete', i < index);
      if (i === index) indicator.setAttribute('aria-current', 'step'); else indicator.removeAttribute('aria-current');
    });
    back.hidden = index === 0;
    next.hidden = index === steps.length - 1;
    submit.hidden = index !== steps.length - 1;
    if (focus) {
      const legend = steps[index].querySelector('legend');
      legend.tabIndex = -1;
      legend.focus({ preventScroll: true });
      document.querySelector('.signup-card').scrollIntoView({ behavior: 'auto', block: 'start' });
    }
  }
  function validateStep(index) {
    for (const input of steps[index].querySelectorAll('input,select')) {
      if (!input.checkValidity()) { showStep(index, false); input.reportValidity(); input.focus(); return false; }
    }
    return true;
  }
  form.noValidate = true;
  next.addEventListener('click', () => { if (validateStep(current)) showStep(current + 1); });
  back.addEventListener('click', () => showStep(current - 1));
  form.addEventListener('submit', event => {
    // Pressing Enter advances the current step without validating hidden fields.
    if (current < steps.length - 1) { event.preventDefault(); if (validateStep(current)) showStep(current + 1); return; }
    for (let i = 0; i < steps.length; i++) {
      if (!validateStep(i)) { event.preventDefault(); return; }
    }
    submit.disabled = true;
    submit.textContent = 'Enviando inscrição…';
  });
  document.querySelectorAll('.form-errors a').forEach(link => link.addEventListener('click', event => {
    const field = document.getElementById(link.getAttribute('href').slice(1));
    const index = steps.findIndex(step => step.contains(field));
    if (index >= 0) { event.preventDefault(); showStep(index, false); field.focus(); }
  }));
  const invalid = form.querySelector('[aria-invalid="true"]');
  const errorBox = document.querySelector('.form-errors');
  const initial = invalid ? steps.findIndex(step => step.contains(invalid)) : 0;
  showStep(Math.max(0, initial), false);
  if (errorBox) { errorBox.focus(); errorBox.scrollIntoView({block:'center'}); }
  window.addEventListener('pageshow', () => { submit.disabled = false; submit.innerHTML = 'Concluir inscrição <span aria-hidden="true">✓</span>'; });
})();
