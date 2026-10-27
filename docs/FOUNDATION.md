# Offline evaluation foundation (phases A–B)

Python 3.11+, standard library only. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m benchmarks --help
.venv/bin/python -m benchmarks status
# Optional: explicit PRIVATE literal config (never implicitly loaded)
.venv/bin/python -m benchmarks status --config /path/to/private-config
```

No command sends inference requests. `paid_dispatch_implemented` is always false. `paid_tests_enabled` reports configuration permission only; ledger `dispatch_allowed` describes accounting readiness, NOT paid authorization. Default status does not read `.env` and needs no key/network. Environment variables override explicit file values. Allowed literal keys are listed in `.env.example`; only exact `true`/`false` flags are accepted. No shell execution/interpolation; duplicate/unknown keys and ambiguous malformed literals fail closed. Do not pass credentials as CLI arguments.

Status creates or resumes `private/ledger.sqlite3` by default (700 directory, 600 file). `--ledger` selects a private path; keep one canonical ledger for the entire approved envelope. Deleting/moving the ledger or deliberately selecting another one would defeat accounting and is not a reset procedure. No reset/release-contingency/raise-limit command exists. Existing policy must match on every reopen; normal restarts retain exposure.

`BudgetLedger(path, stage_limits, total_limit='5.00', stop_line='4.50')` exposes `reserve(stage, upper_usd)`, `settle(id, actual_usd)`, `mark_unknown(id)`, and `summary()`. Money inputs are decimal strings only, conservatively rounded upward to integer microUSD. Limits must already be exact microUSD. Unknown stage/contingency, outstanding request, exhausted stage/total/stop line, and halted accounts refuse reservations. `BEGIN IMMEDIATE` serializes independent processes; transactions close before control returns. Unknown/timeout reservations never expire. Once original usage is verified, `settle` can reconcile unknown requests exactly once. Full overruns are recorded even beyond $5 and permanently halt new reservations. No automatic retry exists.

Remaining/available figures are headroom, not permission to bypass outstanding/unknown/halting checks. Confirmed plus reserved is exposure; unknown is a count, not a zero charge. Generation ID column is reserved for Phase C integration; no usage metadata/network reconciliation is implemented yet.

## Verification record

Implementation used repeated selected-test RED → minimal implementation → full-suite GREEN → explicit-path commits. Real observed REDs included: private plan exclusion, offline CLI missing, nonpositive/oversized budgets accepted, hidden-key presence missing, literal parser absent, money returning zero, stage overspend accepted, total stop line absent, policy changes accepted, both processes reserving, unknown status not retained, timeout exposure missing, settlement not recorded, overruns not halting, roundtrip status flag unsupported, argument values echoed, and fractional-micro limits accepted. Bootstrap configuration and symlink tests initially raised missing-behavior errors rather than clean assertion failures; those are a strict-TDD evidence limitation, not claimed assertion REDs. Additional regression tests verify cumulative settled stage and total limits, unknown reconciliation, invalid-cost retention, permissions, no implicit dotenv load and network prohibition.

The offline CLI was actually run: disabled, key absent, confirmed/reserved/unresolved zero, remaining 4,500,000 microUSD, total cap 5,000,000. This is an empty local accounting ledger, not a provider account/balance measurement. No private `.env` contents were read or changed. No paid APIs, installs of models, deployment, push or merge occurred in this phase.

See DECISIONS.md for owner gates. Client accounting is not an absolute provider invoice guarantee; tariff bounds, billing semantics, delayed usage, dedicated provider-side limits and external key use still need verification before paid work.
