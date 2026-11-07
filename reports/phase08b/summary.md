# Phase 8b — Existing core vs full-text embedding comparison

Status: completed_with_provenance_caveat
UTC: 2026-11-07T21:57:34.385483+00:00

## Alignment and provenance
- original_core_parquet_rows: 22505
- original_core_embedding_shape: [22505, 384]
- original_fulltext_parquet_rows: 3656
- original_fulltext_embedding_shape: [3656, 384]
- fulltext_ids_available_in_core: 3656
- fulltext_explicit_eligible: 3644
- eligible_with_core_vectors_and_abstract_len_ge_20: 3644
- core_id_order_hash: 915e9091136a8bbd3ecc6c89df5503a02ddb2489929d0a1a07d95786146aeab9
- fulltext_id_order_hash: 0bd1d83245ebaef11b19b608a1a67ff9526ed5b696fbc538099f09d1b528dd12
- core_embedding_source_signals: {'file': '03_embeddings_and_clusters.py', 'field_name_occurrences': {'text': 0, 'title': 3, 'text_for_analysis': 0, 'abstract': 3, 'openalex_id': 0}, 'encode_calls': [{'line': 46, 'first_argument_variable': 'texts'}], 'interpretation': 'Static indications only. Confirm actual feature construction in the original script.'}
- matching_cosine: {'median': 1.0, 'p10': 0.96926, 'p90': 1.0}
- shuffled_cosine: {'median': 0.45478, 'p10': 0.28542, 'p90': 0.59803}
- matched_minus_shuffled_median: 0.54522
- alignment_signal: positive

## paired_embedding_comparison
- {'12': {'number_of_documents': 3644, 'ari_between_core_and_fulltext': 0.55265, 'nmi_between_core_and_fulltext': 0.66059, 'core_cosine_silhouette': 0.06023, 'fulltext_cosine_silhouette': 0.04875}, '18': {'number_of_documents': 3644, 'ari_between_core_and_fulltext': 0.49713, 'nmi_between_core_and_fulltext': 0.65336, 'core_cosine_silhouette': 0.05482, 'fulltext_cosine_silhouette': 0.04786}, '25': {'number_of_documents': 3644, 'ari_between_core_and_fulltext': 0.46345, 'nmi_between_core_and_fulltext': 0.65199, 'core_cosine_silhouette': 0.04799, 'fulltext_cosine_silhouette': 0.04806}}

## Interpretation limits
- Core vector provenance must be checked in the original scripts before asserting a title/abstract-only encoding.
- Row order inside each NPY is inferred from corresponding Parquet and checked indirectly by matched-vs-shuffled similarities; no source index file is known.
- Analysis uses only common explicitly accepted full-text publications, avoiding sample-size confounding.
- An embedding comparison cannot independently validate the topical labels or establish policy usefulness.
- No embeddings, copyright text, article metadata or identifiers are published.
