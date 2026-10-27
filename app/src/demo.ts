export interface Effects {
  schedule(fn: () => void, delay: number): number;
  cancel(id: number): void;
  cancelSpeech(): void;
}
export interface Turn {
  transcript: string;
  reply: string;
  requiredCorrection: string;
  optionalSuggestion: string;
  explanationId: string;
}
export interface State { phase: 'idle' | 'holding' | 'processing' | 'ready'; turns: Turn[]; }
export function createDemo(effects: Effects, changed: () => void = () => {}) {
  const state: State = { phase: 'idle', turns: [] };
  let timer: number | undefined;
  let generation = 0;
  function stop() {
    generation++;
    if (timer !== undefined) effects.cancel(timer);
    timer = undefined;
    effects.cancelSpeech();
    state.phase = 'idle';
    changed();
  }
  return {
    stop,
    clear() {
      state.turns = [];
      stop();
    },
    get state(): State { return structuredClone(state); },
    press() {
      if (state.phase === 'holding' || state.phase === 'processing') return;
      state.phase = 'holding';
      changed();
    },
    release() {
      if (state.phase !== 'holding') return;
      state.phase = 'processing';
      const current = ++generation;
      timer = effects.schedule(() => {
        if (current !== generation) return;
        timer = undefined;
        state.turns.push({
          transcript: 'Yesterday I go to the market.',
          reply: 'That sounds nice! What did you buy at the market?',
          requiredCorrection: 'Yesterday I went to the market.',
          optionalSuggestion: 'For more detail: Yesterday I went to the local market to buy fruit.',
          explanationId: 'Kata “yesterday” menunjukkan waktu lampau. Gunakan bentuk lampau “went”, bukan “go”. Tambahan detail hanya saran, bukan kesalahan tata bahasa.',
        });
        state.phase = 'ready';
        changed();
      }, 650);
      changed();
    },
  };
}

// Never select a remote speech service in this offline demo.
export function replay(
  speech: SpeechSynthesis | undefined,
  text: string,
  make: (text: string) => SpeechSynthesisUtterance = text => new SpeechSynthesisUtterance(text),
): 'started' | 'unavailable' {
  if (!speech || !text) return 'unavailable';
  try {
    const voice = speech.getVoices().find(v => v.localService && /^en(?:-|$)/i.test(v.lang));
    if (!voice) return 'unavailable';
    speech.cancel();
    const utterance = make(text);
    utterance.voice = voice;
    utterance.lang = voice.lang;
    speech.speak(utterance);
    return 'started';
  } catch { return 'unavailable'; }
}
