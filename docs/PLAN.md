# BeraniBicara — implementation and evaluation plan

> Architecture update: the owner selected Rust + Tauri 2 + TypeScript instead of SwiftUI. See [TAURI-MIGRATION.md](TAURI-MIGRATION.md) and [DECISIONS.md](DECISIONS.md). Any SwiftUI/Swift-specific steps below are historical proposals and must not be implemented; evaluation, privacy and budget requirements remain applicable.

## Scope and status

Approved direction: public GitHub project for learning and open-source development; native macOS app is the intended delivery target. Current milestone is documentation only. This file describes future work, not completed tests or a working application.

Initial target: English speaking practice, Indonesian explanations. No execution of paid APIs, model installation, service deployment, or automatic paid CI is authorized by this documentation milestone. Repository license remains a separate owner decision.

## User experience

1. User speaks English.
2. App presents the original transcript and allows clarification if recognition is uncertain.
3. Tutor responds conversationally; required grammar corrections and optional style suggestions are separate.
4. App speaks the answer; review can appear after the turn or session.
5. User can replay or stop the audio.

Begin with push-to-talk. Automatic turn detection and interruption handling follow only once the baseline is measured. No pronunciation score in the first version.

## Architecture candidates

### A. Modular pipeline

Mac microphone → STT → tutor LLM → TTS → Mac playback.

- STT candidates: `openai/whisper-large-v3-turbo`, `qwen/qwen3-asr-1.7b`.
- Tutor candidates: `qwen/qwen3.7-flash`, `deepseek/deepseek-v4-flash`.
- TTS candidates: `hexgrad/kokoro-82m` for English; `fish-audio/drama-3` for multilingual evaluation.

Model IDs, availability, endpoint compatibility, billing units, and languages must be rechecked before execution. Kokoro is not assumed to support Indonesian. Drama pricing may be promotional. Public listings do not prove account access or actual quality.

### B. Native speech-to-speech comparator

Evaluate Qwen Realtime through Alibaba only if access and spend are approved. Do not confuse a text-output Qwen Omni endpoint on OpenRouter with a realtime speech-output endpoint.

## Milestone 1 — provider access and accounting

- Inspect existing authorized provider access without exposing secrets.
- Agree on a total test budget and stopping policy before paid requests.
- Re-fetch model catalogs and endpoint documentation; validate billing units explicitly.
- Run minimal authorized STT, tutor, and TTS calls.
- Capture provider/model, request/generation IDs, outcome, usage, and cost without secret-bearing headers or private content in public logs.
- For raw-byte TTS, obtain billing via documented generation metadata when available; missing cost is unknown, never zero.

Deliverable: access matrix and sample call evidence. Stop or select a documented alternative if the intended route fails.

## Milestone 2 — controlled component evaluation

### Grammar and overcorrection

Prepare 100 human-reviewed English text cases: 50 erroneous and 50 grammatical cases. Include tenses, agreement, articles, prepositions, plurals, questions, acceptable spoken forms, and British/American variants. Keep ambiguous cases separate. Reference corrections can have multiple acceptable answers.

Use the same instructions and recorded parameters across tutor candidates; repeat cases to assess variability. Human review remains necessary; an LLM judge alone cannot establish correctness.

Report separately:
- Necessary corrections made correctly.
- Introduced errors or meaning changes.
- False claims of error on grammatical sentences.
- Optional style suggestions correctly labeled.
- Indonesian explanation correctness, accessibility, relevance, and usefulness.

### Indonesian-accented English

Use consented real human English recordings from Indonesian speakers, ideally including the user. A single speaker is a personal smoke test, not population coverage. Start with 20 short recordings, then expand across speakers before general claims.

Include grammatical and ungrammatical speech, pauses, and controlled background noise. Human transcripts preserve actual spoken errors. Measure word error rate and task-level meaning preservation; explicitly inspect dropped negatives, tense endings, and model normalization that hides learner errors. Indonesian-language ASR results are not evidence for Indonesian-accented English.

### Speech synthesis

Use identical English prompts and, where supported, Indonesian prompts. Include questions, negation, numbers, proper nouns, mixed-language material, and slow-reading requests. Blind listening review assesses intelligibility, text fidelity, comfort, pronunciation, and unwanted sounds. No voice cloning without explicit speaker consent.

Deliverable: component findings with failures, examples, limitations, and cost evidence. No invented benchmark scores.

## Milestone 3 — interactive prototype

Build a minimal native Mac client and a lightweight API gateway if required. Gate actual stack/minimum macOS version on the user's Mac chip, RAM, OS, and Xcode availability. SwiftUI is the proposed UI stack, not an already-built artifact.

- Keep server-managed provider keys off distributed apps.
- For a personal bring-your-own-key mode, explicitly design secure local credential storage (Keychain) and never bundle shared keys.
- Separate original transcript, tutor reply, corrections, and optional alternatives.
- Speak only user-facing replies, not internal reasoning or metadata.
- Stream/chunk replies where verified; support cancellation and avoid stale audio.
- Document offline/network error behavior and retries.
- Recordings are not retained by default; disclose provider processing and retention policies.

Deliverable: runnable prototype and real microphone/playback verification on macOS. Linux-only tests cannot verify Mac audio behavior.

## Milestone 4 — end-to-end comparison and decision

Run matched conversations on the modular pipeline and the authorized realtime comparator. Record audio duration, turn count, context policy, network conditions, errors, and model/provider versions.

Measure from user speech end to first audible playback on Mac. Also record turn-detection delay, upload, STT, first tutor output, TTS first audio, and playback buffering where observable. Report median and p95, plus failure rate and test count. Public endpoint latency charts are not controlled application benchmarks.

Account for all STT, LLM, TTS, retries, and comparator costs. Include context/reasoning/cache charges where reported. Separate inference cost from credit-purchase fees, taxes, hosting, and development.

### Proposed acceptance targets (not achieved results)

- Correct necessary grammar correction on at least 90% of unambiguous error cases.
- False error claims on at most 5% of grammatical cases.
- Human-rated Indonesian explanations average at least 4/5.
- End-to-end median at most 2.5 seconds and p95 at most 5 seconds under declared test conditions.
- No silent treatment of missing cost data as zero.
- No critical meaning reversal in the retained evaluation cases without explicitly flagging the failure.

Define denominators, scoring rubric, repetition count, and percentile method before executing. Initial sample sizes give exploratory evidence, not production reliability guarantees. If a target fails, report PARTIAL/INVALIDATED and the limiting condition.

Deliverable: evidence-backed model choice, known limitations, and total per-session cost. Do not keep two architectures unless justified.

## Milestone 5 — project foundation and distribution

Only after feasibility is established:
- Add application structure, unit tests, mocked provider tests, and error handling.
- Add standard GitHub-hosted CI; run Linux-compatible tests where appropriate and macOS build checks when needed.
- No paid API calls on public pull-request CI. Never expose secrets through fork workflows, artifacts, logs, or untrusted code.
- Set workflow permissions narrowly, timeouts, concurrency cancellation, and short artifact retention.
- Default-branch changes follow reviewed branches/PRs after the initial bootstrap.
- Unsigned build artifacts are not equivalent to signed/notarized distribution; handle signing and Apple account requirements separately.

## Out of scope initially

Subscriptions, App Store launch, many languages at once, automatic voice cloning, validated pronunciation scoring, persistent audio collection, and self-hosting large models on the VPS.

## Required inputs before implementation/testing

- Owner approval of test budget and securely configured provider access.
- Mac chip, RAM, macOS, and local testing availability.
- Consented speech samples; no public upload by default.
- Repository license choice (MIT proposed).

## Documentation references (discovery, not runtime proof)

- https://openrouter.ai/docs/guides/overview/multimodal/stt.md
- https://openrouter.ai/docs/guides/overview/multimodal/tts.md
- https://openrouter.ai/api/v1/models
- https://openrouter.ai/docs/cookbook/administration/usage-accounting
- https://www.alibabacloud.com/help/en/model-studio/realtime
- https://arxiv.org/html/2506.13148v1

Recheck these sources before execution; no catalog price is locked in this plan.
