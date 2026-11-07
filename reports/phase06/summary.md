# Phase 6 — Search provenance and full-text denominator audit

Generated: 2026-11-07T21:27:28.683558+00:00

## Corpus stages
- raw: 199366 rows, 103608 unique OpenAlex IDs
- unique: 102822 rows, 102822 unique OpenAlex IDs
- core: 22524 rows, 22524 unique OpenAlex IDs
- refined: 21676 rows, 21676 unique OpenAlex IDs
- ready: 10283 rows, 10283 unique OpenAlex IDs
- screening: 10283 rows, 10283 unique OpenAlex IDs
- fulltext: 3656 rows, 3656 unique OpenAlex IDs
- extracted: 3656 rows, n/a unique OpenAlex IDs

## Raw to unique OpenAlex IDs
- {'raw_distinct_openalex_ids': 103608, 'retained_distinct_openalex_ids': 102822, 'distinct_ids_not_retained': 786, 'not_retained_with_doi_matching_kept_id': 0, 'not_retained_with_missing_doi': 0, 'not_retained_with_distinct_nonempty_doi': 786, 'caution': 'Matching DOI is not conclusive proof of the filtering/deduplication rule.'}

## Retrieval window
- {'valid_dates': 199366, 'total_rows': 199366, 'first_utc_date': '2026-05-25', 'last_utc_date': '2026-05-25', 'distinct_utc_dates': 1}

## Search query log
- 27 recorded queries; see JSON (not yet verified against exact script parameters)

## Download and extraction
- Attempts: {'rows': 5000, 'status_counts': {'downloaded': 3655, 'error_connectionerror': 30, 'error_connecttimeout': 62, 'error_readtimeout': 13, 'error_sslerror': 42, 'error_toomanyredirects': 1, 'exists': 1, 'http_400': 2, 'http_403': 922, 'http_404': 73, 'http_405': 2, 'http_410': 1, 'http_429': 15, 'http_500': 3, 'http_503': 13, 'not_pdf_text/html': 1, 'not_pdf_text/html; charset=utf-8': 29, 'not_pdf_text/html;charset=utf-8': 1, 'too_small': 134}, 'unique_dois': 4835, 'missing_doi': 164, 'unique_nonempty_pdf_paths': 3655, 'missing_pdf_path': 1344}
- Success table: {'rows': 3656, 'status_counts': {'downloaded': 3655, 'exists': 1}, 'unique_dois': 3537, 'missing_doi': 118, 'unique_nonempty_pdf_paths': 3655, 'missing_pdf_path': 0}
- Extraction table: {'rows': 3656, 'status_counts': {'ok': 3656}, 'unique_dois': 3537, 'missing_doi': 118, 'unique_nonempty_pdf_paths': 3655, 'missing_pdf_path': 0, 'nonpositive_text_length': 1}
- Cross-manifest comparison: {'_doi': {'distinct_attempt_keys': 4835, 'distinct_success_keys': 3537, 'success_keys_not_in_attempts': 0, 'success_keys_matching_attempts': 3537}, '_file': {'distinct_attempt_keys': 3655, 'distinct_success_keys': 3655, 'success_keys_not_in_attempts': 0, 'success_keys_matching_attempts': 3655}, 'extraction_vs_success_pdf_paths': {'extracted_unique_paths': 3655, 'success_unique_paths': 3655, 'extracted_paths_not_in_success': 0}}
- Fulltext eligibility: {'excluded_fulltext': 8, 'text_length_nonpositive': 1, 'both': 1, 'retained_after_both_filters': 3648}

## Five-thousand-selection proxy
- {'screen_included_rows': 10265, 'attempt_manifest_rows': 5000, 'attempt_manifest_distinct_dois': 4835, 'included_rows_matching_attempt_doi': 4836, 'included_rows_unmatched_or_no_doi': 5429, 'matching_is_a_proxy': True, 'caution': 'A DOI-based match does not reconstruct the exact 5000 selected OpenAlex records when DOIs are duplicated or missing.', 'relevance_score_median_attempt_doi_match': 14.0, 'relevance_score_median_unmatched': 14.0}

## Methodological warnings
- Recorded query labels and retrieval timestamps do not specify the full API endpoints and filter parameters.
- Full-text extraction record, successful download, usable text, and assigned embedding are separate units.
- DOI-based selected-record matching is incomplete when DOI is missing or duplicated.
- The 786 missing OpenAlex IDs cannot be called duplicates until their removals are attributed to executable rules.
- This analysis does not perform new expert assessment or rerun NLP models.
- All published findings are aggregate. The original research project is unmodified.
