# Phase 12 — Pilot: title/abstract vs BODY-only chunk embeddings

Status: completed_pilot_no_human_validation
UTC: 2026-11-07T22:59:06.856375+00:00

## Source and sampling
{
  "explicitly_eligible_pool": 3644,
  "selected": 240,
  "analyzable_paired": 240,
  "strata_counts": {
    "ai_literacy_training": 19,
    "assessment": 33,
    "equity_access": 18,
    "ethics_integrity": 45,
    "governance_policy": 33,
    "privacy_security": 14,
    "research_scholarship": 23,
    "teaching_learning": 54
  },
  "seed": 20261107
}

## Configuration
{
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "model_max_seq_length": 256,
  "max_body_chunks": 12,
  "first_tokens_excluded": 512,
  "body_end_fraction": 0.85,
  "chunk_content_tokens": 192,
  "chunk_overlap_tokens": 32,
  "chunk_selection": "uniformly spaced over full_text after the first 512 tokens and before the last 15%",
  "pooling": "unweighted mean of normalized chunk vectors then L2 normalization",
  "hybrid": "L2-normalized sum of bibliographic and body vectors",
  "device": "cpu"
}

## Summary
### truncation_avoidance
{'mean_pooled_chunks_per_document': {'min': 7.0, 'p10': 12.0, 'median': 12.0, 'p90': 12.0, 'max': 12.0, 'mean': 11.95}, 'fulltext_wordpiece_tokens': {'min': 1893.0, 'p10': 5492.9, 'median': 6104.5, 'p90': 7069.4, 'max': 24718.0, 'mean': 6394.10833}, 'body_available_wordpiece_tokens': {'min': 1097.0, 'p10': 4156.6, 'median': 4676.0, 'p90': 5496.7, 'max': 20498.0, 'mean': 4922.50833}, 'documents_no_body_after_skip_and_tail': 0, 'chunking_skips_first_tokens': 512, 'model_limit_tokens': 256}
### paired_cosine
{'bibliographic_vs_body_chunks': {'min': 0.1264, 'p10': 0.72331, 'median': 0.82669, 'p90': 0.87361, 'max': 0.92809, 'mean': 0.8013}, 'bibliographic_vs_original_fulltext': {'min': 0.86311, 'p10': 0.96871, 'median': 1.0, 'p90': 1.0, 'max': 1.0, 'mean': 0.99145}, 'body_chunks_vs_original_fulltext': {'min': 0.1264, 'p10': 0.72302, 'median': 0.82583, 'p90': 0.87185, 'max': 0.92126, 'mean': 0.80082}}
### nearest_neighbor_overlap
{'bibliographic_vs_body_chunks': {'top_k': 10, 'overlap_fraction': {'min': 0.0, 'p10': 0.1, 'median': 0.4, 'p90': 0.6, 'max': 0.8, 'mean': 0.36875}}, 'bibliographic_vs_hybrid': {'top_k': 10, 'overlap_fraction': {'min': 0.2, 'p10': 0.4, 'median': 0.6, 'p90': 0.8, 'max': 0.9, 'mean': 0.62458}}}
### kmeans_exploratory
{'12': {'models': {'bibliographic': {'cosine_silhouette_sample': 0.05201, 'min_cluster_size': 7}, 'original_fulltext': {'cosine_silhouette_sample': 0.06056, 'min_cluster_size': 8}, 'body_chunks': {'cosine_silhouette_sample': 0.11494, 'min_cluster_size': 4}, 'hybrid_50_50': {'cosine_silhouette_sample': 0.10786, 'min_cluster_size': 5}}, 'cross_modality': {'bibliographic__original_fulltext': {'ari': 0.24895, 'nmi': 0.47036}, 'bibliographic__body_chunks': {'ari': 0.16953, 'nmi': 0.35678}, 'bibliographic__hybrid_50_50': {'ari': 0.26592, 'nmi': 0.46135}, 'original_fulltext__body_chunks': {'ari': 0.18827, 'nmi': 0.37748}, 'original_fulltext__hybrid_50_50': {'ari': 0.26656, 'nmi': 0.45903}, 'body_chunks__hybrid_50_50': {'ari': 0.39241, 'nmi': 0.57189}}}, '18': {'models': {'bibliographic': {'cosine_silhouette_sample': 0.04903, 'min_cluster_size': 1}, 'original_fulltext': {'cosine_silhouette_sample': 0.06156, 'min_cluster_size': 2}, 'body_chunks': {'cosine_silhouette_sample': 0.10544, 'min_cluster_size': 3}, 'hybrid_50_50': {'cosine_silhouette_sample': 0.09303, 'min_cluster_size': 2}}, 'cross_modality': {'bibliographic__original_fulltext': {'ari': 0.24565, 'nmi': 0.50972}, 'bibliographic__body_chunks': {'ari': 0.15028, 'nmi': 0.44689}, 'bibliographic__hybrid_50_50': {'ari': 0.2024, 'nmi': 0.51211}, 'original_fulltext__body_chunks': {'ari': 0.14786, 'nmi': 0.43489}, 'original_fulltext__hybrid_50_50': {'ari': 0.20994, 'nmi': 0.48833}, 'body_chunks__hybrid_50_50': {'ari': 0.32562, 'nmi': 0.58959}}}, '25': {'models': {'bibliographic': {'cosine_silhouette_sample': 0.03011, 'min_cluster_size': 1}, 'original_fulltext': {'cosine_silhouette_sample': 0.05138, 'min_cluster_size': 1}, 'body_chunks': {'cosine_silhouette_sample': 0.09362, 'min_cluster_size': 1}, 'hybrid_50_50': {'cosine_silhouette_sample': 0.07453, 'min_cluster_size': 1}}, 'cross_modality': {'bibliographic__original_fulltext': {'ari': 0.2041, 'nmi': 0.54668}, 'bibliographic__body_chunks': {'ari': 0.15713, 'nmi': 0.49973}, 'bibliographic__hybrid_50_50': {'ari': 0.21691, 'nmi': 0.55776}, 'original_fulltext__body_chunks': {'ari': 0.14327, 'nmi': 0.51223}, 'original_fulltext__hybrid_50_50': {'ari': 0.22308, 'nmi': 0.56239}, 'body_chunks__hybrid_50_50': {'ari': 0.28437, 'nmi': 0.63984}}}}

## Limitations
- This is an exploratory stratified pilot, not a preregistered confirmatory test.
- Higher silhouette does not imply semantic truth, utility or improved policy classification.
- The first 512 tokens and final 15 percent are excluded as a transparent heuristic, not validated section segmentation.
- Original fulltext vectors were computed by the legacy pipeline and may have truncated to bibliographic prefixes.
- KMeans partitions in a small pilot are unstable; do not replace manuscript topic taxonomy using pilot alone.
- No independent human annotations exist yet; evaluate them before claiming substantive policy relevance.
- New privately cached vectors are NOT added to GitHub; only aggregate metrics are reported.
