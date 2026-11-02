'use strict';
const form = document.querySelector('#ticket-form');
const submit = document.querySelector('#submit');
const output = document.querySelector('#output');
const error = document.querySelector('#error');
const empty = document.querySelector('#empty');
document.querySelectorAll('[data-example]').forEach(button => button.addEventListener('click', () => {
  document.querySelector('#text').value = button.dataset.example;
  document.querySelector('#language').value = 'en';
  document.querySelector('#text').focus();
}));
form.addEventListener('submit', async event => {
  event.preventDefault();
  submit.disabled = true;
  submit.textContent = 'Analizando…';
  output.hidden = true; error.hidden = true; empty.hidden = true;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch('/api/v1/predict', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, signal: controller.signal,
      body: JSON.stringify({text: document.querySelector('#text').value, language: document.querySelector('#language').value})
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(typeof data.detail === 'string' ? data.detail : 'Revisa el texto y el idioma de la solicitud.');
    }
    document.querySelector('#route').textContent = data.label === 1 ? 'Atención financiera humana' : 'Otra ruta de soporte';
    document.querySelector('#explanation').textContent = data.label === 1 ? 'La puntuación alcanza el umbral financiero. Deriva la solicitud al equipo especializado.' : 'La puntuación está por debajo del umbral financiero. Continúa la revisión en soporte general.';
    document.querySelector('#score').textContent = (data.financial_score*100).toFixed(2)+' %';
    document.querySelector('#meter').value = data.financial_score;
    document.querySelector('#threshold').textContent = data.threshold.toFixed(2);
    document.querySelector('#latency').textContent = data.latency_ms.toFixed(2)+' ms';
    document.querySelector('#request-id').textContent = data.request_id.slice(0, 8);
    output.hidden = false;
  } catch (failure) {
    document.querySelector('#error-message').textContent = failure.name === 'AbortError' ? 'El servicio tardó demasiado. Inténtalo de nuevo o solicita revisión humana.' : failure.message;
    error.hidden = false;
  } finally {
    clearTimeout(timer); submit.disabled = false; submit.innerHTML = 'Analizar solicitud <span aria-hidden="true">→</span>';
  }
});
