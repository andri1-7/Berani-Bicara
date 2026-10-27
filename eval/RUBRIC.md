# Human evaluation rubric

Status: evaluation design, not model results. Label examples and review model output without revealing the model name to reviewers. Record unresolved judgments; do not force ambiguous English into one reference.

## Grammar

For each case record original, context/register, acceptable corrections, necessary edits, dialect allowances and reviewer identity (pseudonym allowed). Error cases need at least one necessary grammatical edit; correct cases must permit an empty correction list. A conversational fragment can be valid in context.

Score required corrections as correct only when they fix the necessary issue without introducing a new issue or materially changing the intended meaning. If several answers are acceptable, do not use exact-string matching alone. A style rewrite labeled optional is not a false grammar accusation; calling a valid sentence wrong is.

Report these denominators separately:

- Necessary correction success: successful reviewed error cases / all unambiguous reviewed error cases.
- False-error claims: reviewed grammatical cases incorrectly declared wrong / all reviewed grammatical cases.
- Introduced errors and meaning changes: explicit case counts and examples with permission.
- Unreviewed, failed, malformed and ambiguous cases: separate counts, never silently drop them.

## Indonesian explanations

Rate each dimension 1–5: linguistic correctness, understandable Indonesian, relevance, usefulness of the example. Anchors: 1 = misleading/unusable; 3 = partly helpful but requires revision; 5 = correct, concise and accessible to a beginner. Reviewer must read the original and correction, not just the fluent explanation. Report dimension means and sample counts; do not present model self-ratings as human review.

## Accented English

Use consented human recordings with human verbatim reference transcripts, preserving learner errors. Report word error rate with a documented normalization policy. Inspect critical negations, names, tense/plural endings and intent separately. ASR accuracy is not pronunciation quality. English spoken by an Indonesian speaker is distinct from Indonesian-language ASR. Do not infer population reliability from one voice.

## TTS

Use matched source texts and supported language/voice settings. Blind listening checks word fidelity, intelligibility, correct negation/numbers, comfort and useful slow delivery. If a language is unsupported, mark N/A. Expressiveness alone does not prove suitability for a tutor.

## Runtime and cost

Measure from speech end to playback start on a real Mac; distinguish response bytes received from audio heard. Include failed turns in failure rate, report sample count, median and percentile definition. Record per-request generation ID, stage, provider, bounded reservation and confirmed cost privately. Missing cost is UNKNOWN and keeps its reservation. No quality claim is established by a mock or demo fixture.
