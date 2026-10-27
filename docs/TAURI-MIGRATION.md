# Desktop implementation: Rust + Tauri 2

Owner selected Rust + Tauri with HTML/CSS/TypeScript instead of SwiftUI. This supersedes the Swift-specific implementation/build steps in `PLAN.md` and the original private implementation plan; Python offline evaluation stays in place.

## Targets and boundaries

- First target: Apple Silicon MacBook Pro M2, 8 GB, macOS Sonoma 14.2.
- Windows/Linux remain future targets, not verified compatibility claims.
- Frontend: `app/src/`, vanilla TypeScript, HTML and CSS with Vite.
- Rust host: `app/src-tauri/`, Tauri 2 commands with narrowly scoped capabilities.
- No shared API key in the frontend, source, bundle, localStorage or CI artifact.
- Personal BYOK integration will use OS secret storage through Rust; it is not implemented merely because the demo runs.
- No model inference on the VPS. Do not install Linux WebKit development stacks or build Rust desktop binaries here just to claim Mac validation.

## Incremental implementation

1. Offline conversation state machine with deterministic fixtures and tests; demo banner mandatory.
2. Frontend controls for demo turn, Stop, replay and session clear. Never label demo fixtures as transcription or model results.
3. Minimal Tauri host and narrow command surface. No filesystem/shell/network plugin permission without a concrete tested feature.
4. Verify frontend tests and production assets locally; verify Rust/Tauri compile on macOS runner or user's Mac.
5. Verify actual macOS microphone permission/capture/format, cancellation and playback before connecting live speech.
6. Add Rust-mediated provider access and secure credential storage only after offline budget fixes and live-access gates are resolved.
7. Supervised real session validates grammar feedback, accents, audio latency and cost; mocks do not establish quality.

A browser-based speech-synthesis demo is not a measured OpenRouter TTS result. Browser speech APIs are runtime-dependent and may use OS services. The demo must handle absence without claiming generated audio or billable model usage.

## Verification commands

From repository root once scaffolding exists:

```bash
cd app
npm ci
npm test
npm run build
```

On Mac with verified compatible Rust and Xcode command-line tools:

```bash
cd app
npm ci
npm run tauri dev
```

Exact Rust test/build commands depend on the created manifest; record actual results, not expected success. No claim of Mac app launch until tested on a Mac. Confirm the selected toolchain supports Sonoma 14.2 rather than blindly installing the newest Xcode.

## CI design

Use standard GitHub-hosted macOS runner for native checks and Ubuntu for Python/frontend checks when appropriate. Pin reviewed action commits. CI requires no OpenRouter secret and must never call paid endpoints. Read-only workflow permissions, finite timeouts, cancellation and short artifact retention. Initial CI should build a preview, not automatically publish releases or request signing secrets.

References: https://v2.tauri.app/start/prerequisites/ and https://v2.tauri.app/distribute/pipelines/github/ . Documentation establishes prerequisites, not successful runtime behavior.
