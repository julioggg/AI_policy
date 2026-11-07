# Phase 4 — Source and topic sensitivity

Generated: 2026-11-07T21:10:32.578005+00:00

## Populations (journal selection is a proxy, NOT peer-review verification)
- included_all: 10265
- included_journal_article_review: 7216
- fulltext_all: 3656
- fulltext_journal_article_review: 2992
- fulltext_eligible: 3648
- fulltext_eligible_journal_article_review: 2985

## Topic and policy distribution shifts
### included_all -> included_journal_article_review
- disciplinary_area: TV=0.03182, JS(bits)=0.00167, max change(pp)=3.16
- policy_dimension: TV=0.02358, JS(bits)=0.00052, max change(pp)=1.8
- publication_year: TV=0.03026, JS(bits)=0.00081, max change(pp)=2.52
- source_type: TV=0.28436, JS(bits)=0.15926, max change(pp)=28.44
- type: TV=0.14769, JS(bits)=0.07811, max change(pp)=14.77
### fulltext_all -> fulltext_journal_article_review
- disciplinary_area: TV=0.02613, JS(bits)=0.00072, max change(pp)=2.61
- policy_dimension: TV=0.01228, JS(bits)=0.00021, max change(pp)=0.92
- publication_year: TV=0.03535, JS(bits)=0.00122, max change(pp)=2.76
- source_type: TV=0.16904, JS(bits)=0.09016, max change(pp)=16.9
- type: TV=0.09655, JS(bits)=0.05005, max change(pp)=9.66
- kmeans_12: TV=0.03285, JS(bits)=0.00167, max change(pp)=1.77
- kmeans_18: TV=0.03922, JS(bits)=0.00189, max change(pp)=1.52
- kmeans_25: TV=0.03814, JS(bits)=0.0025, max change(pp)=1.17
### fulltext_all -> fulltext_eligible
- disciplinary_area: TV=0.00021, JS(bits)=0.0, max change(pp)=0.02
- policy_dimension: TV=0.00071, JS(bits)=0.0, max change(pp)=0.05
- publication_year: TV=0.0002, JS(bits)=0.0, max change(pp)=0.02
- source_type: TV=0.00025, JS(bits)=0.0, max change(pp)=0.02
- type: TV=0.00027, JS(bits)=0.0, max change(pp)=0.03
- kmeans_12: TV=0.00104, JS(bits)=0.0, max change(pp)=0.06
- kmeans_18: TV=0.00144, JS(bits)=0.0, max change(pp)=0.07
- kmeans_25: TV=0.00169, JS(bits)=0.0, max change(pp)=0.07
### fulltext_eligible -> fulltext_eligible_journal_article_review
- disciplinary_area: TV=0.02627, JS(bits)=0.00073, max change(pp)=2.63
- policy_dimension: TV=0.01209, JS(bits)=0.00021, max change(pp)=0.89
- publication_year: TV=0.03551, JS(bits)=0.00123, max change(pp)=2.75
- source_type: TV=0.16913, JS(bits)=0.09021, max change(pp)=16.91
- type: TV=0.09677, JS(bits)=0.05016, max change(pp)=9.68
- kmeans_12: TV=0.03299, JS(bits)=0.00168, max change(pp)=1.78
- kmeans_18: TV=0.03915, JS(bits)=0.00189, max change(pp)=1.52
- kmeans_25: TV=0.03839, JS(bits)=0.00251, max change(pp)=1.17
### included_all -> fulltext_all
- disciplinary_area: TV=0.02785, JS(bits)=0.00152, max change(pp)=2.77
- policy_dimension: TV=0.03021, JS(bits)=0.00099, max change(pp)=2.25
- publication_year: TV=0.02298, JS(bits)=0.0007, max change(pp)=2.22
- source_type: TV=0.11769, JS(bits)=0.01486, max change(pp)=11.53
- type: TV=0.05113, JS(bits)=0.01023, max change(pp)=4.6

## Quality checks
- {'kmeans_18_missing_labels': 0, 'kmeans_18_unique_labels': 18, 'kmeans_18_suspect_rows_by_label': {'topic_3': 3, 'topic_11': 2, 'topic_8': 1, 'topic_2': 1, 'topic_13': 1}, 'screening_categories': {'Include_core': 9264, 'Include_policy': 899, 'Include_context': 102}, 'excluded_fulltext_count': 8, 'nonpositive_text_length': 1, 'excluded_and_textless_overlap': 1, 'valid_fulltext_count': 3648}

## Interpretation constraints
- OpenAlex source_type=journal and type=article/review is a journal-indexed proxy, NOT verified peer-review.
- A genuine peer-reviewed-only analysis needs journal and publication version verification.
- Changes in topic proportions across subsets do not demonstrate superiority of any KMeans solution.
- Removing fulltext exclusions and textless records does not constitute human screening.
- No document-level or copyrighted textual data have been exported.
