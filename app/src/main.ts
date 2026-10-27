import { createDemo, replay } from './demo';
import './style.css';

const conversation = document.querySelector<HTMLDivElement>('#conversation')!;
const status = document.querySelector<HTMLParagraphElement>('#status')!;
const audioStatus = document.querySelector<HTMLParagraphElement>('#audio-status')!;
const talk = document.querySelector<HTMLButtonElement>('#talk')!;
const replayButton = document.querySelector<HTMLButtonElement>('#replay')!;
const speech = 'speechSynthesis' in window ? window.speechSynthesis : undefined;
const fallback = 'Suara Inggris lokal tidak tersedia. Baca balasan di atas; tidak ada audio yang diunduh.';
let playbackGeneration = 0;
const demo = createDemo({
  schedule: (fn, delay) => window.setTimeout(fn, delay),
  cancel: id => window.clearTimeout(id),
  cancelSpeech: () => {
    // Cancellation may invoke utterance callbacks synchronously.
    playbackGeneration++;
    speech?.cancel();
    audioStatus.textContent = 'Pemutaran dihentikan.';
  },
}, render);
function paragraph(label: string, text: string, className = '') {
  const block = document.createElement('div');
  block.className = className;
  const heading = document.createElement('h3'); heading.textContent = label;
  const body = document.createElement('p'); body.textContent = text;
  block.append(heading, body);
  return block;
}
function render() {
  const { phase, turns } = demo.state;
  status.textContent = {
    idle: 'Siap untuk simulasi. Tidak merekam audio.',
    holding: 'Simulasi tombol ditahan — bukan merekam. Lepaskan untuk contoh.',
    processing: 'Menyiapkan contoh tetap di perangkat…',
    ready: 'Contoh selesai. Ini bukan evaluasi ucapan Anda.',
  }[phase];
  talk.setAttribute('aria-pressed', String(phase === 'holding'));
  talk.disabled = phase === 'processing';
  replayButton.disabled = turns.length === 0 || phase === 'holding' || phase === 'processing';
  conversation.replaceChildren();
  if (!turns.length) conversation.append(paragraph('Mulai dengan contoh', '“Yesterday I go to the market.” akan muncul setelah simulasi.'));
  for (const turn of turns) {
    const article = document.createElement('article');
    article.append(
      paragraph('Anda · transkrip contoh asli', turn.transcript, 'original'),
      paragraph('Partner · balasan contoh', turn.reply, 'reply'),
      paragraph('Koreksi wajib · grammar', turn.requiredCorrection, 'correction'),
      paragraph('Saran opsional · bukan kesalahan', turn.optionalSuggestion, 'suggestion'),
      paragraph('Mengapa? · Bahasa Indonesia', turn.explanationId),
    );
    conversation.append(article);
  }
}
talk.addEventListener('pointerdown', event => {
  if (event.button !== 0) return;
  talk.setPointerCapture(event.pointerId);
  demo.press();
});
talk.addEventListener('pointerup', () => demo.release());
talk.addEventListener('pointercancel', () => demo.stop());
talk.addEventListener('keydown', event => {
  if ((event.key === ' ' || event.key === 'Enter') && !event.repeat) { event.preventDefault(); demo.press(); }
});
talk.addEventListener('keyup', event => {
  if (event.key === ' ' || event.key === 'Enter') { event.preventDefault(); demo.release(); }
});
talk.addEventListener('blur', () => { if (demo.state.phase === 'holding') demo.stop(); });
document.querySelector('#stop')!.addEventListener('click', () => demo.stop());
document.querySelector('#clear')!.addEventListener('click', () => demo.clear());
replayButton.addEventListener('click', () => {
  const text = demo.state.turns.at(-1)?.reply ?? '';
  // Invalidate the previous playback before replay() can call speech.cancel().
  const current = ++playbackGeneration;
  audioStatus.textContent = replay(speech, text, text => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onend = () => { if (current === playbackGeneration) audioStatus.textContent = 'Pemutaran selesai.'; };
    utterance.onerror = () => { if (current === playbackGeneration) audioStatus.textContent = fallback; };
    return utterance;
  }) === 'started' ? 'Meminta pemutaran suara lokal… Jika tidak terdengar, baca teks balasan.' : fallback;
});
window.addEventListener('blur', () => demo.stop());
window.addEventListener('pagehide', () => demo.clear());
render();
