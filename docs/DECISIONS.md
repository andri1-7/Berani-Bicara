# Evaluation foundation decisions

- Implement only the offline Python standard-library evaluation foundation now. No provider adapter, inference, deployment, model install or Mac application is included.
- Intended preview: native Mac, bring your own key in Keychain; no shared public backend or bundled VPS key.
- English practice first, Indonesian explanations; preserve original transcripts and separate required corrections from optional style. No pronunciation grading.
- The approved envelope is $5 TOTAL, not recurring. Operational stop line is $4.50 including reservations. Stages: smoke $0.25, grammar $0.75, transcription $0.75, tts $0.75, conversation $1.00. Contingency $1.50 is locked; unused allocations never transfer automatically.
- Persist exact integer microUSD, round costs conservatively upward, serialize reservations with SQLite. Unknown/timeout costs retain exposure; an overrun records the full cost and permanently halts dispatch. No reset, limit-change or contingency-release command is provided.
- Client reservations cannot guarantee an invoice ceiling: delayed billing, inaccurate tariff bounds and external use of the key require provider-side limits and reconciliation before any paid run.
- Mac target is confirmed: MacBook Pro 13-inch M2 (2022), 8 GB RAM, Sonoma 14.2 (see `MAC-VALIDATION.md`). Owner gates remain unresolved: Xcode and real microphone/playback access, license choice, consented recordings, existing balance, dedicated key/provider-side cap and auto-recharge readback, verified tariffs/route billing/voices. No paid run is authorized by this implementation.
- Private configuration is opt-in via an explicit path; normal offline status does not read `.env`. Errors and status must not reveal secrets or untrusted values.
