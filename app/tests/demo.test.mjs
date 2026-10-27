import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemo } from '../.test-build/demo.js';

function harness() {
  let tasks = new Map(), next = 0, cancelledSpeech = 0;
  const effects = {
    schedule(fn) { const id = ++next; tasks.set(id, fn); return id; },
    cancel(id) { tasks.delete(id); },
    cancelSpeech() { cancelledSpeech++; },
  };
  const demo = createDemo(effects);
  return { demo, tasks, get cancelledSpeech() { return cancelledSpeech; },
    tick() { const pending = [...tasks.values()]; tasks.clear(); pending.forEach(fn => fn()); } };
}

test('new session is idle with no conversation or credentials', () => {
  const { demo } = harness();
  assert.deepEqual(demo.state, { phase: 'idle', turns: [] });
});

test('hold and release produces one canned turn with separate feedback', () => {
  const h = harness();
  h.demo.press();
  assert.equal(h.demo.state.phase, 'holding');
  h.demo.press();
  h.demo.release();
  assert.equal(h.demo.state.phase, 'processing');
  h.demo.release();
  assert.equal(h.tasks.size, 1);
  h.tick();
  const state = h.demo.state;
  assert.equal(state.phase, 'ready');
  assert.equal(state.turns.length, 1);
  assert.equal(state.turns[0].transcript, 'Yesterday I go to the market.');
  assert.equal(state.turns[0].requiredCorrection, 'Yesterday I went to the market.');
  assert.ok(state.turns[0].reply);
  assert.ok(state.turns[0].optionalSuggestion);
  assert.match(state.turns[0].explanationId, /lampau/);
});

test('stop cancels pending work and speech, including a stale callback', () => {
  const h = harness();
  h.demo.press(); h.demo.release();
  const stale = [...h.tasks.values()][0];
  h.demo.stop();
  assert.equal(h.tasks.size, 0);
  assert.equal(h.cancelledSpeech, 1);
  stale();
  assert.deepEqual(h.demo.state, { phase: 'idle', turns: [] });
  h.demo.press(); h.demo.stop(); h.demo.release(); h.tick();
  assert.equal(h.demo.state.turns.length, 0);
});

test('clear removes text and invalidates old work without mutating snapshots', () => {
  const h = harness();
  h.demo.press(); h.demo.release(); h.tick();
  const snapshot = h.demo.state;
  h.demo.press(); h.demo.release();
  const stale = [...h.tasks.values()][0];
  h.demo.clear(); stale(); h.tick();
  assert.deepEqual(h.demo.state, { phase: 'idle', turns: [] });
  assert.equal(h.tasks.size, 0);
  snapshot.turns[0].transcript = 'changed externally';
  assert.equal(h.demo.state.turns.length, 0);
  h.demo.press(); h.demo.release(); h.tick();
  assert.equal(h.demo.state.turns.length, 1);
  assert.equal(h.demo.state.turns[0].transcript, 'Yesterday I go to the market.');
});

test('replay uses only explicitly local English voices or returns an honest fallback', async () => {
  const { replay } = await import('../.test-build/demo.js');
  assert.equal(replay(undefined, 'hello'), 'unavailable');
  const spoken = [];
  const remote = { lang: 'en-US', localService: false };
  const local = { lang: 'en-GB', localService: true };
  const speech = { getVoices: () => [remote], cancel() {}, speak: u => spoken.push(u) };
  const make = text => ({ text });
  assert.equal(replay(speech, 'hello', make), 'unavailable');
  assert.equal(spoken.length, 0);
  speech.getVoices = () => [remote, local];
  assert.equal(replay(speech, 'hello', make), 'started');
  assert.equal(spoken[0].voice, local);
  assert.equal(spoken[0].text, 'hello');
});
