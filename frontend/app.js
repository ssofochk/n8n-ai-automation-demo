const form = document.querySelector('#calculator');
const submit = document.querySelector('#submit');
const result = document.querySelector('#result');
let pending = false;
const symbols = {add: '+', subtract: '−', multiply: '×', divide: '÷'};
function show(state, message, value) {
  result.dataset.state = state;
  result.replaceChildren();
  if (state === 'loading') {
    const spinner = document.createElement('span');
    spinner.className = 'spinner-border text-danger'; spinner.setAttribute('aria-hidden','true'); result.append(spinner);
  }
  if (state === 'success') {
    const number = document.createElement('div'); number.className = 'result-value'; number.textContent = String(value); result.append(number);
  }
  const text = document.createElement('p'); text.textContent = message;
  if (state === 'error') { text.className = 'alert alert-danger'; text.setAttribute('role','alert'); }
  result.append(text);
}
function validate(input) {
  const raw = input.value.trim();
  const valid = /^[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:e[+-]?\d+)?$/i.test(raw) && Number.isFinite(Number(raw.replace(',', '.')));
  const message = !raw ? 'Please enter a number.' : !valid ? 'Please enter a valid number.' : '';
  input.classList.toggle('is-invalid', !!message); input.setAttribute('aria-invalid', String(!!message));
  document.getElementById(input.id + '-error').textContent = message;
  return !message;
}
for (const input of [document.getElementById('a'), document.getElementById('b')]) input.addEventListener('input', () => { if (input.classList.contains('is-invalid')) validate(input); });
form.addEventListener('submit', async event => {
  event.preventDefault();
  if (pending) return;
  const inputs = [document.getElementById('a'), document.getElementById('b')];
  const invalid = inputs.filter(input => !validate(input));
  if (invalid.length) { invalid[0].focus(); return; }
  const [a,b] = inputs.map(input => Number(input.value.trim().replace(',', '.')));
  const operation = form.querySelector('input[name=operation]:checked').value;
  pending = true; submit.disabled = true; submit.textContent = 'Calculating…'; form.setAttribute('aria-busy','true');
  show('loading', 'Calculating your answer…');
  try {
    const response = await fetch('/api/calculate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({a,b,operation})});
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(typeof data.detail === 'string' && response.status === 400 ? data.detail : 'Something went wrong. Please try again.');
    }
    const data = response.status === 204 ? null : await response.json();
    if (data?.result == null) { show('empty','No result returned. Please try again.'); return; }
    if (typeof data.result !== 'number' || !Number.isFinite(data.result)) throw new Error('Invalid result. Please try again.');
    show('success', `${a} ${symbols[operation]} ${b} = ${data.result}`, data.result);
  } catch (error) { show('error', error instanceof TypeError ? 'Connection failed. Please try again.' : error.message); }
  finally { pending = false; submit.disabled = false; submit.textContent = 'Calculate ♡'; form.removeAttribute('aria-busy'); }
});
