# BeraniBicara — OFFLINE DEMO

Rust + Tauri v2 shell with a Vite / vanilla TypeScript frontend. The existing Python evaluator is unchanged. This is a foundation, **not a working speech tutor**.

## Run

```sh
cd app
npm ci
npm test
npm run build
npm run dev            # browser demo, localhost:1420
npm run tauri -- dev   # requires Rust and platform prerequisites
```

For the primary MacBook Pro M2 / Sonoma 14.2 target, follow the official [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/) before desktop development. No Rust toolchain or platform dependencies were installed here. macOS execution, signing, packaging, microphone access and webview playback are **unverified**. Bundle generation is disabled until release identity/assets are chosen. The identifier is a demo placeholder, not a registered release identity.

## What the controls actually do

- Hold the demo button (pointer, Space or Enter), then release: a 650 ms local timer inserts one fixed English transcript, reply, required grammar correction, optional detail suggestion and Indonesian explanation. No microphone is accessed.
- Replay requests browser speech synthesis **only with a voice marked localService and English**. No remote voice or audio API is used. Missing voices, unsupported APIs or playback errors leave the visible text and an explicit fallback. Actual OS voice behavior still needs offline Mac validation.
- Stop cancels pending demo timers and browser speech; a generation token rejects already-queued stale callbacks. Existing conversation stays visible.
- Clear cancels work and removes all conversation text. Blur stops work; pagehide clears the session.

## Privacy / scope

No API key entry, provider integration, paid inference, microphone entitlement, network client, persistence, analytics, downloads or pronunciation grading. State exists only in memory; no localStorage or files. Vite `envDir: false` prevents development/build from loading `.env`. Package installation is a development network operation, not an application feature. Vite development HMR uses localhost networking; production CSP denies connections and external resources. No custom environment access is used.

The only Rust command, `health`, returns the constant `offline-demo`; it is registered but not invoked by this UI. No plugins are installed, capability permissions are empty, and no remote capability scope is granted. Official Tauri documentation says registered application commands are available by default; this is not a guessed `allow-health` permission. CSP intentionally does not enable frontend IPC, since the demo does not need it.

## Verification

`npm test` compiles the state module and uses Node's built-in test runner (no test framework dependency). Tests cover transitions, duplicate press/release, Stop and stale callback cancellation, Clear/restart, isolated state snapshots and local-only speech fallback. Each behavior slice was observed RED before implementation, then GREEN. The Rust health unit test is included but **not executed** because Cargo is absent, including `/root/.cargo/bin/cargo`.

Browser smoke checks exercised hold/release, feedback, replay fallback, Clear, Stop during pending work, and empty localStorage. Browser behavior is not proof of compatibility with the actual macOS webview.

Official references used before scaffolding:
- https://v2.tauri.app/start/create-project/
- https://v2.tauri.app/security/capabilities/
- https://v2.tauri.app/develop/calling-rust/

Ignored outputs: `node_modules/`, `dist/`, `.test-build/`, `src-tauri/target/`, `src-tauri/gen/`. Commit source and `package-lock.json`, not generated build directories. No commits were made.
