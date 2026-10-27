# Offline evaluation foundation

Current status: offline configuration and persistent budget accounting are implemented. A passing budget test is not proof of provider billing semantics or API access. No paid transport is enabled.

## Run without credentials or network

From repository root on Linux/Python 3.11+:

```bash
python3 -m venv .venv
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m benchmarks --help
.venv/bin/python -m benchmarks status
```

No external Python packages are required. Tests use temporary databases and synthetic fixtures. Normal status does not implicitly load `.env`. The CLI creates/uses the private ledger at `private/ledger.sqlite3`; it is not a read-only database inspection command.

To inspect whether private configuration is populated without exposing it:

```bash
.venv/bin/python -m benchmarks status --config .env
```

Only booleans and accounting totals are returned. Never print `.env`, paste it into chat, or include it in an artifact. `paid_dispatch_implemented` remains false. A ledger's `dispatch_allowed` means only that accounting has headroom; it does NOT enable API calls or prove access/balance.

## Budget semantics

Amounts ending `_micro` are integer millionths of a US dollar. The ledger persists confirmed costs, reserved exposure and unresolved requests. A request must reserve its conservative upper cost bound before future transport can send it. Only one request can remain unsettled at a time across processes. Timeouts/unknown costs keep reservations and block new ones. A settlement exceeding its reservation records actual exposure and permanently halts the ledger.

The configured envelope is $5 total with $4.50 operational stop. Existing stage caps sum to $3.50; the $1.50 contingency is deliberately locked. The remaining $0.50 near the total ceiling is headroom, not a second spending allowance. Raising caps, releasing contingency or changing providers requires a deliberate reviewed decision; there is no automatic transfer/reset command.

Do not delete/replace/move the production ledger to recover budget. The database is local accounting, not provider-side enforcement; copies do not coordinate with each other. Dedicated key limits, external-key-use checks, price bounds and provider usage reconciliation remain required before live tests.

## Known constraints

- This is not a Mac application or a live model benchmark.
- No grammar or accented-English quality has been measured by mocked tests.
- No CLI command purchases credit, hosts a model, or calls a paid endpoint.
- Refer to `BUDGET.md`, `PLAN.md`, `MAC-VALIDATION.md` and `../eval/RUBRIC.md` for gates and human validation.
