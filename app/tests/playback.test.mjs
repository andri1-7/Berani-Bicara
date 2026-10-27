import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';

// Exercise the actual UI handlers without a browser or speech service.
function harness() {
  class Element {
    textContent = '';
    disabled = false;
    listeners = new Map();
    addEventListener(name, fn) { this.listeners.set(name, fn); }
    fire(name, event = {}) { this.listeners.get(name)?.(event); }
    setAttribute() {}
    append() {}
    replaceChildren() {}
  }
  const elements = new Map();
  const document = {
    querySelector(selector) {
      if (!elements.has(selector)) elements.set(selector, new Element());
      return elements.get(selector);
    },
    createElement: () => new Element(),
  };
  const spoken = [];
  const tasks = new Map();
  let nextTimer = 0;
  let onCancel = () => {};
  const speech = {
    getVoices: () => [{ lang: 'en-US', localService: true }],
    cancel: () => onCancel(),
    speak: utterance => spoken.push(utterance),
  };
  const window = {
    speechSynthesis: speech,
    setTimeout(fn) { const id = ++nextTimer; tasks.set(id, fn); return id; },
    clearTimeout: id => tasks.delete(id),
    addEventListener() {},
  };
  const context = vm.createContext({
    document, window, structuredClone,
    SpeechSynthesisUtterance: class { constructor(text) { this.text = text; } },
  });
  for (const file of ['demo', 'main']) {
    const source = readFileSync(new URL(`../src/${file}.ts`, import.meta.url), 'utf8')
      .replace(/^import .*;\n/gm, '').replace(/^export /gm, '');
    const { outputText } = ts.transpileModule(source, {
      compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None },
    });
    vm.runInContext(outputText, context, { filename: `${file}.ts` });
  }
  const click = id => document.querySelector(`#${id}`).fire('click');
  const talk = document.querySelector('#talk');
  talk.fire('keydown', { key: 'Enter', preventDefault() {} });
  talk.fire('keyup', { key: 'Enter', preventDefault() {} });
  for (const fn of tasks.values()) fn();
  tasks.clear();
  return {
    click, spoken,
    get status() { return document.querySelector('#audio-status').textContent; },
    set onCancel(fn) { onCancel = fn; },
  };
}

test('replacement replay ignores old callbacks but accepts current completion and errors', () => {
  const h = harness();
  h.click('replay');
  const old = h.spoken[0];
  h.click('replay');
  const requesting = h.status;
  old.onend();
  assert.equal(h.status, requesting);
  old.onerror();
  assert.equal(h.status, requesting);
  h.spoken[1].onend();
  assert.equal(h.status, 'Pemutaran selesai.');
  h.spoken[1].onerror();
  assert.match(h.status, /Suara Inggris lokal tidak tersedia/);
});

test('Clear keeps its audio status when cancelled speech later ends or errors', () => {
  const h = harness();
  h.click('replay');
  const old = h.spoken[0];
  h.click('clear');
  old.onend();
  assert.equal(h.status, 'Pemutaran dihentikan.');
  old.onerror();
  assert.equal(h.status, 'Pemutaran dihentikan.');
});

for (const action of ['stop', 'clear', 'replay']) {
  test(`${action} invalidates callbacks before synchronous speech cancellation`, () => {
    const h = harness();
    h.click('replay');
    const old = h.spoken[0];
    const before = h.status;
    let cancellations = 0;
    h.onCancel = () => {
      cancellations++;
      old.onend();
      assert.equal(h.status, before, 'onend must not write during cancel()');
      old.onerror();
      assert.equal(h.status, before, 'onerror must not write during cancel()');
    };
    h.click(action);
    assert.equal(cancellations, 1);
    assert.equal(h.status, action === 'replay' ? before : 'Pemutaran dihentikan.');
  });
}

test('Stop keeps its audio status when cancelled speech later ends or errors', () => {
  const h = harness();
  h.click('replay');
  const old = h.spoken[0];
  h.click('stop');
  assert.equal(h.status, 'Pemutaran dihentikan.');
  old.onend();
  assert.equal(h.status, 'Pemutaran dihentikan.');
  old.onerror();
  assert.equal(h.status, 'Pemutaran dihentikan.');
});
