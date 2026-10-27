# Live API gate — NOT APPROVED FOR DISPATCH YET

The owner approved $5 TOTAL inference, but endpoint-level safety and accounting still need verification. No checkbox below is implied by a nonempty key or passing offline tests.

- [ ] Independent foundation review findings fixed and re-reviewed.
- [ ] Explicit ledger initialization separated from read-only status; no automatic accounting reset.
- [ ] Dedicated OpenRouter key belongs to this project, with no external concurrent usage.
- [ ] Nonresetting $5 provider key limit and relevant account/workspace budget read back through authorized settings.
- [ ] Existing credit balance is sufficient; no purchase/top-up is performed without separate approval.
- [ ] Auto-recharge disabled and verified.
- [ ] STT/TTS tariff minimums, rounding and route exposure checked.
- [ ] Owner understands STT/TTS route order/only/ignore are not enforced by documented audio endpoints. Current catalog maxima are estimates, not certified request price ceilings.
- [ ] If a dependable upper bound remains unavailable, do not dispatch. Any estimate-based exception requires an explicit owner risk decision; the $5 approval alone does not waive this gate.
- [ ] Tutor reasoning disabled if supported; output bound and structured response behavior verified, no automatic repair/retry.
- [ ] Voice ID/default and language support confirmed for selected TTS.
- [ ] Human recording consent and verbatim transcript available privately.
- [ ] Raw TTS generation metadata reconciliation implemented and tested; missing/finally uncertain cost retains reservation and blocks new spend.
- [ ] CLI requires explicit local enable plus manual allow-paid invocation, and all inference paths reserve first.
- [ ] No paid calls in public pull-request CI and no shared owner key in Mac app.

## Stop behavior

Failure, timeout, missing generation ID or unverified cost does not release reserved exposure. Pause rather than auto-retry. Any actual charge above reservation is persisted and halts further inference. Missing data is UNKNOWN, never zero.

## Current status

Provider documentation research and offline contract work are available; authenticated account settings and model quality have not been verified. Live provider transport is not enabled. See `PROVIDERS.md` and `BUDGET.md`.
