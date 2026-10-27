# Target Mac and validation gate

## Confirmed target

User-provided About This Mac image confirms MacBook Pro 13-inch (M2, 2022), 8 GB unified memory, macOS Sonoma 14.2. Serial numbers are deliberately not recorded. Proposed native build target is arm64 with minimum macOS 13, pending actual build verification. Models run via provider APIs; no large local model installation is required.

## Unknown prerequisites

- Available Xcode and Swift toolchain on the user's Mac.
- Available disk capacity (not shown in the image).
- Owner's ability to download and manually test an unsigned developer preview.
- License approval before an open-source release.

Do not recommend updating macOS or installing the newest Xcode blindly: first check supported OS/toolchain combinations. CI can compile on a newer macOS runner, but that does not prove microphone/playback behavior or deployment compatibility on Sonoma 14.2.

## Verification worksheet (not yet executed)

Record commit, device/OS, test date and tester. Mark each item PASS, FAIL or BLOCKED; do not treat a build success as a completed microphone test.

- App bundle launches on target Mac without embedded credentials.
- Demo mode works without network and is visibly labeled DEMO.
- Microphone request explains audio processing; denial produces an actionable error.
- Permission grant allows bounded recording; empty input makes no paid request.
- Private test audio remains out of Git and artifacts.
- Transcript remains separate from required corrections and optional alternatives.
- A user turn receives audible English speech; Indonesian explanations are readable.
- Stop cancels at recording, transcription, tutor, synthesis and playback stages.
- Late provider results cannot resume cancelled playback.
- Invalid credentials, offline network, timeout and exhausted evaluation budget are handled without automatic paid retries.
- Replay does not call synthesis again when local audio is already available.
- Clear session and quit remove temporary audio; no recording retention by default.
- Keychain save/read/delete works and key never appears in logs.
- Timing distinguishes speech end, audio bytes received and playback started.

## Budget boundary

The owner's $5 test envelope is shared with VPS evaluation, not a new $5 per device. A public BYOK app must never bundle the VPS key. Live Mac evaluation needs the plan's shared budget enforcement or a separately verified transfer/reconciliation arrangement. Until then use offline/demo tests only.
