# Evaluation budget proposal

Status: PROPOSED. This document is not authorization to purchase credits, call paid APIs, or configure account billing. Currency: USD; no exchange-rate assumption.

## Scope

One controlled feasibility evaluation, not a recurring subscription or a production monthly budget. Initial path uses OpenRouter STT, tutor, and TTS. Alibaba realtime is optional and requires separate explicit approval; it does not silently consume an additional allowance.

## Recommended limits

- Total inference ceiling: $5 across all evaluated providers combined.
- Stage 1 access/billing smoke tests: $0.25.
- Stage 2 grammar and Indonesian explanation comparison: $0.75.
- Stage 3 consented speech transcription comparison: $0.75.
- Stage 4 English/Indonesian TTS listening comparison: $0.75.
- Stage 5 complete conversation sessions: $1.00.
- Contingency held back: $1.50. It is not available automatically; release requires owner approval within the same $5 ceiling.

Unused stage allocations do not automatically transfer. Stop at a stage cap and request a decision. Provider access or correctness failure is a reason to stop, not to run larger tests.

## Payment versus inference

The $5 ceiling is for inference charges only. Buying $5 of credit can cost more because of credit-purchase fees, payment fees, or taxes. Before any purchase, show the actual checkout amount and obtain separate owner approval. No automatic top-ups, no recurring purchase, no VPS upgrade, no paid GitHub runner, no signing purchase, and no model hosting are included.

## Enforcement design (must be implemented and tested first)

1. Create a dedicated project API key with a $5 provider-side credit limit where supported. Do not reset or raise the limit automatically; disable auto-recharge. Confirm actual settings through provider readback when available.
2. The test harness has a persistent, atomic USD ledger shared by all runs. It records stage, model/provider, request ID, confirmed cost, unresolved requests, and reserved maximum cost. Never store secrets or private recordings in public logs.
3. Start sequentially: at most one paid request in flight. Never run a full matrix concurrently during initial verification.
4. Before each request, establish a conservative upper cost bound from the selected provider tariff, input duration/size, maximum output tokens, bounded context, rounding/minimum charges, and any reference-audio or reasoning charges. Reserve that amount atomically before sending. Disable automatic model/provider fallbacks that could change the price unexpectedly. If a dependable bound is unavailable, stop for review.
5. Do not dispatch when confirmed charges plus outstanding reservations plus the next reservation would exceed either the stage cap or the operational stop line of $4.50. The remaining $0.50 is a reconciliation buffer inside the $5 ceiling, not extra spending permission.
6. Reconcile using actual usage and documented generation metadata. Release unused reservations only after the cost is known. If cost is missing, keep the reservation and pause; missing cost is not zero. Compare ledger totals with provider account/key usage.
7. A timeout or cancelled stream does not prove that upstream billing stopped. Reconcile the original request before retrying. No automatic paid retries during initial evaluation.
8. Every new process resumes the existing ledger. Restarting the program must not reset the budget. Keep local credentials and the private ledger out of Git.
9. Paid tests run manually only, never from a public PR or scheduled CI. Mocked tests must verify stage-cap refusal, total-cap refusal, restart persistence, concurrent-dispatch refusal, missing-cost pause, and timeout reconciliation before real API calls.

These are planned safeguards, not an existing guarantee. Provider billing may be delayed and provider limits may not be instantaneous. Never promise an absolute invoice cap based solely on a client-side counter; retain headroom and verify provider semantics before approval.

## Test sizing

- Begin with one short request per required endpoint, verifying cost units and account access.
- Expand grammar/overcorrection tests toward the 100-case plan only if reservations fit the approved stage budget.
- Start audio with 20 short consented human recordings; broaden speaker coverage later. Personal recordings remain private.
- Start TTS with matched short English prompts; add Indonesian only for supported voices/models.
- Complete sessions begin short and expand to longer sessions only after the measured per-session cost fits the remaining stage allocation.
- The budget cap wins over sample-size targets. Report incomplete coverage explicitly, never extrapolate a completed benchmark from a small smoke test.

## Required owner decisions before spending

- Approve or change the $5 total inference ceiling and stage allocations.
- Approve the actual credit-purchase total separately if new credit is required.
- Configure the dedicated key securely, not in Discord, Git, or app source.
- Approve use and processing of any supplied voice recordings.

## Outcomes

Publish sanitized findings: model/provider identity, sample counts, quality limitations, median/p95 playback latency when measured on Mac, confirmed inference costs, unknown charges, and remaining budget. Do not publish private transcripts/audio by default. Any additional evaluation budget requires a fresh explicit decision.
