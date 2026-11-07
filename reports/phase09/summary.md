# Phase 9 — Forensic examination of embedding provenance

UTC: 2026-11-07T22:01:13.803025+00:00

Paired accepted records: 3644

## Numerical identity of existing vectors
- Component-wise exact equality: 2502
- max absolute component difference <= 1e-7: 2502
- cosine >= 0.999999: 2502
- cosine >= 0.999: 2553
- cosine < 0.90: 49
- cosine quantiles: {'median': 1.0, 'p10': 0.9692643, 'p90': 1.0, 'min': 0.7244761, 'max': 1.0}
- raw-vector L2-distance quantiles: {'median': 0.0, 'p10': 0.0, 'p90': 0.2479332, 'min': 0.0, 'max': 0.742326}

## Text-length summaries
- abstract: {'rows': 3644, 'zero_length': 0, 'median_characters': 1534, 'p10_characters': 1002, 'p90_characters': 2306, 'max_characters': 6000}
- full_text: {'rows': 3644, 'zero_length': 0, 'median_characters': 30003, 'p10_characters': 22223, 'p90_characters': 30003, 'max_characters': 30003}
- topic_text: {'rows': 3644, 'zero_length': 0, 'median_characters': 15993, 'p10_characters': 11910, 'p90_characters': 16000, 'max_characters': 16000}
- semantic_text: {'rows': 3644, 'zero_length': 0, 'median_characters': 15993, 'p10_characters': 11910, 'p90_characters': 16003, 'max_characters': 16003}
- combined_text: {'rows': 3644, 'zero_length': 0, 'median_characters': 31549, 'p10_characters': 23961, 'p90_characters': 32292, 'max_characters': 36154}
- core_abstract: {'rows': 3644, 'zero_length': 0, 'median_characters': 1534, 'p10_characters': 1002, 'p90_characters': 2306, 'max_characters': 27772}
- core_text_for_analysis: {'rows': 3644, 'zero_length': 0, 'median_characters': 1639, 'p10_characters': 1104, 'p90_characters': 2419, 'max_characters': 27878}
- core_text: {'rows': 3644, 'zero_length': 0, 'median_characters': 2009, 'p10_characters': 1397, 'p90_characters': 2813, 'max_characters': 28378}

## Text-prefix overlap
- core_text_for_analysis_vs_topic_text: {'exact_text_match': 0, 'identical_first_256_characters': 3642, 'identical_first_512_characters': 3628, 'core_first_128_characters_found_in_topic_head': 3644, 'compared_records': 3644}
- core_abstract_vs_topic_text: {'exact_text_match': 0, 'identical_first_256_characters': 0, 'identical_first_512_characters': 0, 'core_first_128_characters_found_in_topic_head': 3643, 'compared_records': 3644}
- core_title_vs_topic_text: {'exact_text_match': 0, 'identical_first_256_characters': 3, 'identical_first_512_characters': 1, 'core_first_128_characters_found_in_topic_head': 3644, 'compared_records': 3644}

## Original script inspection (static indications)
- 03_embeddings_and_clusters.py: [{'line': 46, 'argument_is_named_variable': True, 'argument_variable_references_whitelisted_fields': ['abstract', 'title']}]
- 12_fulltext_screening_and_extraction.py: [{'line': 131, 'argument_is_named_variable': False, 'argument_variable_references_whitelisted_fields': []}, {'line': 139, 'argument_is_named_variable': True, 'argument_variable_references_whitelisted_fields': []}, {'line': 140, 'argument_is_named_variable': True, 'argument_variable_references_whitelisted_fields': []}, {'line': 141, 'argument_is_named_variable': True, 'argument_variable_references_whitelisted_fields': []}]
- 16_fulltext_topic_modeling_umap_hdbscan.py: [{'line': 61, 'argument_is_named_variable': False, 'argument_variable_references_whitelisted_fields': []}]
- 18_fulltext_topic_modeling_kmeans_robust.py: []

## Limitations
- High cosine similarity alone does not imply identical vectors; raw component equality is tested separately.
- Identical embeddings can arise from identical or truncated inputs; these summaries do not prove which mechanism occurred.
- Full-text extraction can exist without full-text representation in the model; both pipeline stages must be audited.
- The original sentence-transformer model, tokenizer and max_seq_length must be verified locally before making a truncation claim.
- The script exports no document identifiers, full texts, abstracts, vectors or article titles.
