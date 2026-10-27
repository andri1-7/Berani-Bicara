# Provider research notes — paid dispatch remains blocked

## Evidence and scope

These notes summarize documentation research checked at **2026-10-27T07:03:43Z**. The research inspected public documentation and unauthenticated catalog/endpoint snapshots; it made no authenticated or paid requests and read no secrets. This document adds no live verification. Source links below provide provenance; none imply authenticated endpoint validation.

**Catalog snapshots are estimates, not a certified upper cost guarantee. Do not use the latest public price list alone to enable paid traffic.** A currently advertised maximum does not lock tariffs, routing, minimum charges, rounding, or delayed settlement.

## Critical routing and budget-bound blocker

The STT and TTS guides explicitly say `provider.order`, `provider.only`, and `provider.ignore` are **not applied**. Documented supported audio provider fields are data-policy constraints and `provider.options`. Do not assume `allow_fallbacks`, `max_price`, a model suffix, or `provider.options` pins an audio route or enforces a price ceiling.

Being able to read, deserialize, or send a `max_price` field is not evidence that the selected audio endpoint applies it. This review did not establish an enforced per-request STT/TTS `max_price` contract. Likewise, reading endpoint `pricing` fields establishes advertised rates only, not a server-enforced bound.

Whisper Turbo can use a more expensive Groq route; Kokoro can use a more expensive Together route. Choosing the cheapest route's rate under-reserves. Taking the maximum across all currently eligible routes is a better estimate, but remains vulnerable to discovery/dispatch changes and unverified billing semantics.

Required safety posture from the report:

- Keep paid dispatch disabled when a dependable upper bound is required and cannot be proven. Represent an unknown upper bound as **unavailable**, not zero or a guessed multiplier.
- An explicitly approved estimate-based experiment must use maxima over every potentially eligible endpoint, bound inputs locally, reserve before sending, serialize inference, avoid automatic retries, and halt on unresolved charges or charges exceeding reservations. This does not turn the estimate into a guarantee.
- An authorized owner must configure and read back a dedicated **nonresetting** key limit and applicable workspace budget. Public docs describe key limits as hard caps, but this research did not authenticate settings or establish STT/TTS preauthorization and delayed-settlement coverage.
- Treat the **$4.50 stop line as confirmed spend plus all outstanding reservations**. The remaining $0.50 is not permission to exceed the $5 total.
- If strict guarantees remain unavailable, stop or obtain an explicit revised risk decision rather than relabeling conservative estimates as guaranteed bounds.

Sources: [STT guide](https://openrouter.ai/docs/guides/overview/multimodal/stt), [TTS guide](https://openrouter.ai/docs/guides/overview/multimodal/tts), [key-cap guide](https://openrouter.ai/docs/guides/best-practices/capping-shared-agent-keys).

## Exact audio endpoint contracts

### Speech to text (STT)

`POST https://openrouter.ai/api/v1/audio/transcriptions`

JSON request shape documented in the report:

```json
{
  "model": "openai/whisper-large-v3-turbo",
  "input_audio": {"data": "<raw-base64-audio>", "format": "wav"},
  "language": "en",
  "response_format": "json"
}
```

The model above is an example candidate, not a locked route. Multipart requests are also supported.

- Success is JSON containing `text` and optional `usage`; `usage.cost` is USD. Preserve transcript text verbatim. Capture `X-Generation-Id` case-insensitively.
- Multipart has a **25 MB** cap. Larger base64 handling is described for OpenAI/Groq adapters, not universally for every provider.
- The **60-second upstream processing timeout is not a recording-duration limit**. Enforce the project's validated **30-second mono WAV** limit locally.
- `prompt` is accepted but ignored in normalized multipart requests. `text`, `srt`, and `vtt` response formats are rejected. `verbose_json` and timestamps depend on provider/model.
- Catalog `context_length=0` does not mean zero audio is allowed.

Source: [STT guide](https://openrouter.ai/docs/guides/overview/multimodal/stt).

### Text to speech (TTS)

`POST https://openrouter.ai/api/v1/audio/speech`

Example using the catalog-listed Kokoro voice:

```json
{
  "model": "hexgrad/kokoro-82m",
  "input": "<bounded tutor reply only>",
  "voice": "af_heart",
  "response_format": "mp3"
}
```

- Use a verified voice where required. **Do not reuse this voice for Drama 3 or invent its default/voice identifier.** Drama 3's voice contract remains unresolved.
- Omit `speed` and `instructions` unless support is established for the route/model.
- A successful response is **raw audio, not JSON**. Check status and `Content-Type`; errors are JSON. Capture `X-Generation-Id` before reading the audio body.
- Public generic output formats are `mp3` and `pcm`; the default is `pcm`. Request `mp3` explicitly when needed.
- No universal input-character limit is documented. Multi-turn array input is currently Gemini-only at this endpoint, despite Drama 3's model-level multi-speaker capability.

Source: [TTS guide](https://openrouter.ai/docs/guides/overview/multimodal/tts).

### Streaming: native capability is not verified OpenRouter support

A model or direct provider advertising native streaming, low latency, or multi-speaker capability does **not** establish that the OpenRouter audio endpoint exposes that capability live. Receiving a raw audio HTTP body also does not prove incremental synthesis, a realtime session API, or cancellation-safe billing. The supplied report did not exercise authenticated OpenRouter streaming or establish a streaming request/response contract for these candidates. Treat actual OpenRouter live streaming support as **unverified**, separately from model-native capabilities and separately from cost reconciliation.

## Advertised audio tariffs and reservation estimates

All values below are **USD per stated native unit**, from the report's endpoint snapshots. The maximum column is only the maximum **advertised in that snapshot**, not a certified upper charge.

| Model | Billing unit | Advertised route rates | Snapshot maximum rate |
| --- | --- | --- | --- |
| `openai/whisper-large-v3-turbo` | Input-audio second | `deepinfra/us`: `0.00000333`; `groq`: `0.0000111111111111` | `0.0000111111111111` / second |
| `qwen/qwen3-asr-1.7b` | Input-audio second | `deepinfra/us`: `0.0000075` | `0.0000075` / second |
| `qwen/qwen3-asr-0.6b` (optional variant) | Input-audio second | `deepinfra/us`: `0.00000333` | `0.00000333` / second |
| `hexgrad/kokoro-82m` | Input character, **not token** | `deepinfra/us`: `0.00000062`; `together`: `0.000004` | `0.000004` / character |
| `fish-audio/drama-3` | **UTF-8 input byte** | `fish-audio`: `0.000002` | `0.000002` / byte, promotional effective rate |

### STT qualifications

- Whisper Turbo estimate: `max(10, ceil(validated_audio_seconds)) * 0.0000111111111111`, rounded upward to ledger precision. Groq documents a ten-second minimum billed length; whether OpenRouter passes it through, and DeepInfra/OpenRouter rounding/minimum rules, were not established. This formula is **not** a certified bound.
- Qwen ASR 1.7B estimate: `ceil(validated_audio_seconds) * 0.0000075`, subject to unknown minimum/rounding rules. A single advertised route is not a routing lock. DeepInfra independently lists `0.00045 USD/minute`; direct-provider pricing is not an OpenRouter contract.

Sources: [Whisper endpoints](https://openrouter.ai/api/v1/models/openai/whisper-large-v3-turbo/endpoints), [Groq audio limitations](https://console.groq.com/docs/speech-to-text#audio-file-limitations), [Qwen 1.7B endpoints](https://openrouter.ai/api/v1/models/qwen/qwen3-asr-1.7b/endpoints), [Qwen 0.6B endpoints](https://openrouter.ai/api/v1/models/qwen/qwen3-asr-0.6b/endpoints), [Qwen model](https://openrouter.ai/qwen/qwen3-asr-1.7b), [DeepInfra Qwen](https://deepinfra.com/Qwen/Qwen3-ASR-1.7B/api).

### TTS qualifications and promotions

- Kokoro estimate: `count(input) * 0.000004` only with a verified common character-count definition. Unicode counting semantics, minimum charges, and a model-specific enforced length limit were not established. ASCII-only evaluation avoids character ambiguity; UTF-8 byte counting is a conservative estimate for common character definitions, **not documented Kokoro billing semantics**.
- Kokoro's catalog `context_length=4096` is not proof of an audio-endpoint character limit. `af_heart` is listed in `supported_voices`. Indonesian is not among its listed languages.
- DeepInfra's direct Kokoro page lists `0.99 USD/M characters` while OpenRouter advertises `0.62 USD/M characters` for `deepinfra/us`. Do not substitute direct-provider tariffs for OpenRouter tariffs.
- Drama 3 estimate: `len(final_input.encode('utf-8')) * 0.000002`, **including inline direction tags**. Graphemes and Unicode code points are not its billing unit.
- Drama 3 advertises **80% off**; its endpoint returns `prompt=0.000002` and `discount=0.8`. The advertised effective rate is **already $2/M bytes**. **Do not apply the discount twice.** Promotion expiry was not established; do not rely on its continuation for a bound.
- Drama 3 minimum charges, maximum input bytes, and explicit preset/default voice contract were not established. `supported_voices=null` does not prove a default voice exists. Retrieved general Fish docs describe older models and cannot establish Drama 3-specific limits.

Sources: [Kokoro endpoints](https://openrouter.ai/api/v1/models/hexgrad/kokoro-82m/endpoints), [Kokoro model](https://openrouter.ai/hexgrad/kokoro-82m), [DeepInfra Kokoro](https://deepinfra.com/hexgrad/Kokoro-82M/api), [Drama 3 model](https://openrouter.ai/fish-audio/drama-3), [Drama 3 endpoints](https://openrouter.ai/api/v1/models/fish-audio/drama-3/endpoints), [Fish TTS docs](https://docs.fish.audio/developer-guide/core-features/text-to-speech).

## Tutor: Qwen Flash routing, reasoning, and schema uncertainty

The report identifies **`qwen/qwen3.7-flash`** as the candidate explicitly named in `docs/PLAN.md`. Do not silently substitute another Qwen Flash model.

Use `POST https://openrouter.ai/api/v1/chat/completions` with explicit `max_tokens`, bounded prompt/history, no tools/plugins, and `reasoning: {"enabled": false}`. Unlike the audio routing contract, chat routing supports endpoint selection: use the full endpoint slug in `provider.only`, `allow_fallbacks=false`, and require supported parameters rather than assuming unsupported controls apply.

Advertised rates are USD per native token; cache-write values are separate advertised rates, not a blanket discount:

| Minimum prompt tokens | Endpoint | Prompt / token | Completion / token | Cache write / token, if reported |
| --- | --- | --- | --- | --- |
| `0` | `alibaba` | `0.00000003` | `0.00000013` | `0.000000038` |
| `0` | `alibaba/us-east-1` | `0.0000000345` | `0.0000001495` | Not reported |
| `32000` | `alibaba` | `0.0000001` | `0.0000004` | `0.000000125` |
| `32000` | `alibaba/us-east-1` | `0.000000115` | `0.00000046` | Not reported |
| `256000` | `alibaba` | `0.0000002` | `0.0000008` | `0.00000025` |
| `256000` | `alibaba/us-east-1` | `0.00000023` | `0.00000092` | Not reported |

For a reservation, use the **applicable route-specific context tier**, not the cheapest base rate. Across the reported routes and tiers, advertised prompt/completion maxima are `0.00000023` / `0.00000092` per token; these snapshot maxima are not an authenticated billing guarantee. Reported catalog limits: context `1000000`, maximum prompt `983616`, maximum completion `65536` tokens. These are not suggested application budgets.

- Reserve input plus capped output using a validated **native-token upper bound**, including message/schema overhead. A character heuristic is not proof.
- Reasoning defaults on in the current catalog and is billed as output. `exclude=true` hides reasoning; it does **not** disable it. Request disabling explicitly, but actual upstream output-cap behavior and reasoning controls were not exercised here.
- Both endpoint records advertise `response_format`, but neither lists `structured_outputs`. **Strict JSON-schema enforcement is unverified.** Validate locally; do not automatically pay for repair attempts.
- Tokenization overhead, exact schema support, and effective upstream output-cap behavior remain unverified. No authenticated guarantee was established.

Sources: [Qwen Flash endpoints](https://openrouter.ai/api/v1/models/qwen/qwen3.7-flash/endpoints), [model catalog](https://openrouter.ai/api/v1/models), [chat provider selection](https://openrouter.ai/docs/guides/routing/provider-selection), [reasoning tokens](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).

## Generation reconciliation: account cost, not upstream cost

For audio requests, persist the reservation and `X-Generation-Id` immediately, including when audio reception is subsequently cancelled. When separately authorized for live access, retrieve:

```text
GET https://openrouter.ai/api/v1/generation?id=<generation-id>
```

Use the same authorized account. Read **`data.total_cost` as the OpenRouter account charge**, verify returned ID/model and appropriate `api_type` (`tts` for speech synthesis; generation metadata recognizes both `tts` and `stt`), and retain provider metadata. STT's optional `usage.cost` is also USD, but missing usage is not a zero-cost signal.

Do not substitute `upstream_inference_cost` for the amount charged to the OpenRouter account; the usage-accounting docs say generation metadata exposes upstream cost only for BYOK. The generation GET is metadata retrieval, not inference. No separate inference charge is documented, but this research did **not** authenticate or exercise reconciliation.

Fail closed on a missing generation header, missing/null cost, not-found metadata, transport failure, or uncertain settlement finality: keep the request unresolved and block new inference. Explicit zero can be accepted only when actually reported and accepted as settled; never infer zero from absence. Cancellation, timeout, or receipt of some audio does not release a reservation. No finalization SLA or immutable-settlement marker was established, so merely receiving metadata is not proof that delayed charges cannot change.

Sources: [generation metadata API](https://openrouter.ai/docs/api/api-reference/generations/get-request-&-usage-metadata-for-a-generation), [generation SDK reference](https://openrouter.ai/docs/client-sdks/python/sdks/generations/README), [usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting).

## Unresolved before paid enablement

1. An enforceable audio routing/price bound, or an explicit owner-approved change from strict guarantees to residual-risk experimentation.
2. Verified provider-side cap coverage, nonresetting key/workspace settings, preauthorization, and delayed billing behavior.
3. Audio minimum-charge and rounding rules; Kokoro Unicode billing semantics and enforceable length limits.
4. Drama 3 promotion expiry, maximum input bytes, and documented default or verified voice ID.
5. TTS settlement finality and safe reservation release conditions.
6. Qwen native-token overhead, effective output/reasoning controls, and strict schema support.
7. Actual OpenRouter live streaming support, if the application requires it; model-native support is insufficient evidence.

These are research blockers, not claims that implementation or live verification has been completed. No paid-enablement decision should be inferred from this document.
