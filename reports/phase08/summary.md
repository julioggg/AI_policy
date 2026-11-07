# Phase 8 — Paired abstract/fulltext experiment

Status: blocked_missing_offline_model
UTC: 2026-11-07T21:39:23.531984+00:00

## Alignment preflight
- model: sentence-transformers/all-MiniLM-L6-v2
- source_rows: 3656
- explicit_accepted_with_nonzero_text: 3644
- excluded_or_unclear_rows: 12
- missing_abstract_in_accepted: 0
- stored_embedding_shape: [3656, 384]
- row_order_sha256: bc8387f3951c92adcee80f755bc44b6c03e8230207abd8a8c527bc2ea0df0a75
- embedding_source_field: topic_text
- encoding_offline: True
- error_type: RuntimeError

## Interpretation constraints
- The existing fulltext embeddings must match the topic_text field; alignment is checked on a random sample.
- Automated policy_dimension labels are weak proxy outcomes, NOT human-validated ground truth.
- Predictive comparisons cannot establish regulatory or educational policy value without expert validation.
- Random unsupervised topic IDs have no intrinsic semantic meaning; use ARI/NMI only for label agreement.
- Both modalities are evaluated on the same subset to avoid corpus-size confounding.
- No private embeddings or copyrighted texts are exported.
