# Phase 2 — Provenance and representativeness

Date UTC: 2026-11-07T20:41:29.650075+00:00

## Corpus counts
- raw: 199366 rows
- deduplicated: 102822 rows
- core: 22524 rows
- q1_refined: 21676 rows
- article_ready: 10283 rows
- screening: 10283 rows
  - screening: {'include_core': 9264, 'include_policy': 899, 'include_context': 102, 'exclude': 18}
- fulltext: 3656 rows
  - screening: {'include_core': 3519, 'include_policy': 124, 'include_context': 13}
  - nonpositive text length: 1
- fulltext_kmeans: 3656 rows
  - screening: {'include_core': 3519, 'include_policy': 124, 'include_context': 13}
  - nonpositive text length: 1
- extracted: 3656 rows
  - nonpositive text length: 1

## Stage containment (OpenAlex IDs)
- raw -> deduplicated: shared 102822; child outside parent 0
- deduplicated -> core: shared 22524; child outside parent 0
- core -> q1_refined: shared 21676; child outside parent 0
- q1_refined -> article_ready: shared 10283; child outside parent 0
- article_ready -> screening: shared 10283; child outside parent 0
- screening -> fulltext: shared 3656; child outside parent 0
- article_ready -> fulltext: shared 3656; child outside parent 0
- fulltext -> fulltext_kmeans: shared 3656; child outside parent 0

## Full text retrieval
- {'attempts': 5000, 'statuses': {'http_403': 922, 'downloaded': 3655, 'http_404': 73, 'too_small': 134, 'error_sslerror': 42, 'error_connecttimeout': 62, '[other]': 30, 'error_connectionerror': 30, 'error_readtimeout': 13, 'http_429': 15, 'http_503': 13}, 'other_status_total': 11, 'unique_dois': 4835, 'matched_fulltext_dois': 3537}

## Embeddings
- {'shape': [3656, 384], 'dtype': 'float32', 'first_128_vectors_finite': True}

## Previously saved KMeans metrics
- {'k': 12.0, 'silhouette_cosine_sample': 0.05905936285853386, 'davies_bouldin': 3.789302435261666, 'calinski_harabasz': 70.78704833984375}
- {'k': 18.0, 'silhouette_cosine_sample': 0.04462435469031334, 'davies_bouldin': 3.906539527652682, 'calinski_harabasz': 53.504478454589844}
- {'k': 25.0, 'silhouette_cosine_sample': 0.03601225093007088, 'davies_bouldin': 3.8371131309677, 'calinski_harabasz': 42.60254669189453}

## Observable sample differences
- Not calculated; recognized include label was not present.

This is an aggregate audit, not independent validation of screening or topics.
