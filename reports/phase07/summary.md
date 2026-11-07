# Phase 7 — Original program rule and edge-case audit

UTC: 2026-11-07T21:41:17.726216+00:00

## OpenAlex attrition
- {'not_retained': {'distinct_openalex_records': 786, 'with_nonempty_abstract': 601, 'no_abstract': 185, 'publication_year_counts': {'2025': 337, '2024': 164, '2023': 130, '2026': 79, '2022': 32, '2021': 23, '2020': 21}, 'type_counts': {'[other]': 769, '[rare combined]': 7, 'article': 10}}, 'retained_from_initial_distinct_ids': {'distinct_openalex_records': 102822, 'with_nonempty_abstract': 97891, 'no_abstract': 4931, 'publication_year_counts': {'2025': 44984, '2024': 24202, '2026': 16883, '2023': 11269, '2022': 2721, '2021': 1710, '2020': 1053}, 'type_counts': {'[other]': 731, '[rare combined]': 10, 'article': 82263, 'book': 1383, 'book-chapter': 2922, 'dissertation': 607, 'editorial': 372, 'other': 1154, 'preprint': 7543, 'report': 668, 'review': 5169}}, 'note': 'Classification of the 786 lost IDs by metadata does NOT establish the causal filter or why it was applied.'}

## PDF path collision
- {'success_rows': 3656, 'unique_nonempty_pdf_paths': 3655, 'duplicated_pdf_path_groups': 1, 'duplicated_pdf_path_group_properties': [{'records': 2, 'all_dois_identical': True, 'all_titles_identical': False, 'statuses': {'downloaded': 1, 'exists': 1}}], 'note': 'No PDF paths or document identifiers are disclosed. Shared path does not prove independent PDF contents.'}

## Fulltext quality decisions
- {'records': 3656, 'ft_decisions': {'include_meta_candidate': 2722, 'include_core_fulltext': 911, 'include_policy_fulltext': 11, 'exclude_fulltext': 7, 'unclear_fulltext': 4, 'exclude_fulltext_unusable': 1}, 'explicit_acceptances': 3644, 'unclear_needs_manual_review': 4, 'explicit_exclusions': 8, 'nonpositive_text_length': 1, 'accepted_with_nonpositive_text_length': 0, 'unclear_with_nonpositive_text_length': 0, 'unrecognized_other': 0, 'note': 'Unclear cases are NOT validated eligible; only a human evaluation can adjudicate them.'}

## Query counts
- {'number_of_logged_queries': 27, 'queries_with_positive_results': 12, 'queries_with_zero_results': 15, 'sum_raw_hits_across_queries': 199366, 'note': 'Summing query hits double-counts overlaps; 24,000 may reflect a per-query cap.'}

## Static inspection of original scripts (operations only)
- 01_collect_openalex.py: 12 whitelisted operations
- 02_prepare_policy_corpus.py: 13 whitelisted operations
- 04_refine_q1_outputs.py: 25 whitelisted operations
- 05_article_ready_package.py: 39 whitelisted operations
- 07_ai_assisted_screening.py: 27 whitelisted operations
- 10_download_open_access_pdfs.py: 14 whitelisted operations
- 11_extract_fulltext_from_pdfs.py: 3 whitelisted operations
- 12_fulltext_screening_and_extraction.py: 19 whitelisted operations
- 16_fulltext_topic_modeling_umap_hdbscan.py: 22 whitelisted operations
- 18_fulltext_topic_modeling_kmeans_robust.py: 16 whitelisted operations

Operations and line numbers are static source-code indications, not proof of executed decisions.
All user-authored source files remain in the original CEDIA project.
