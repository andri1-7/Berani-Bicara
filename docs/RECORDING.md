# Private recording evaluation inputs

No real user recordings have been evaluated yet. `eval/RUBRIC.md` defines scoring; this page only describes input handling.

Use recordings from consenting human English speakers. State the audio will be processed by selected external AI providers and whether it will be kept. A consent boolean in a manifest records an operator assertion; it is not independently verified legal consent. Do not publish another person's speech without permission. Synthetic speech cannot establish Indonesian-accent recognition coverage.

Keep recordings and their real manifest under ignored `recordings/` or `private/`. Never commit personal recordings, transcripts, speaker names or serial numbers. Use pseudonymous IDs. Do not send API keys through Discord.

Each JSONL row has these fields (example metadata only; the path must refer to your own local file):

```json
{"id":"sample01","speaker_id":"speaker01","audio_path":"voice.wav","consent":true,"reference_text":"Yesterday I go home.","language":"en","accent":"Indonesian","device":"Mac microphone","noise":"quiet"}
```

`audio_path` is relative to a private recording root. Absolute paths, `..`, symlinks and missing files are rejected. The verbatim human transcript must preserve grammar errors and negation. Do not replace it with an AI-corrected sentence. Limit clips to 30 seconds for initial tests; audio format/duration validation belongs to the STT adapter, not manifest validation.

Local manifest checks neither upload audio nor prove that the file is valid WAV. A future dispatcher must reopen paths securely at use time; do not assume an earlier path check prevents later filesystem changes. Only trusted local operators may control the recording directory.

Paid evaluation remains disabled until budget and endpoint safeguards are verified. Do not upload a manifest to a provider wholesale; only the approved recording for the current reserved request is transmitted.
