# Phase 3 — KMeans robustness

Generated: 2026-11-07T20:49:56.970389+00:00

Source: {'all_embeddings': 3656, 'zero_or_missing_text_length': 1, 'fulltext_exclusion_flags': 8, 'overlap_invalid_and_excluded': 1, 'clean_subset': 3648, 'row_order_verified_for_two_parquet_tables': True, 'existing_label_columns': ['kmeans_12', 'kmeans_18', 'kmeans_25']}

## Stability and sensitivity

### k = 12
- seed ARI: {'mean': 0.5781, 'median': 0.54702, 'min': 0.48913, 'max': 0.71639, 'std': 0.07354}
- seed NMI: {'mean': 0.67626, 'median': 0.65291, 'min': 0.61116, 'max': 0.75968, 'std': 0.05157}
- resampling ARI full: {'mean': 0.574, 'median': 0.56927, 'min': 0.52115, 'max': 0.64172, 'std': 0.04063}
- refit cosine silhouette: 0.054929
- refit Davies–Bouldin: 3.854116
- refit Calinski–Harabasz: 73.45516
- original model label agreement: {'original_clusters': 12, 'adjusted_rand_original_vs_refit': 0.41536, 'nmi_original_vs_refit': 0.53621}
- exclusion sensitivity: {'clean_rows': 3648, 'excluded_or_textless_rows': 8, 'ari_full_vs_clean_fit_on_retained': 0.58663, 'nmi_full_vs_clean_fit_on_retained': 0.67927}

### k = 18
- seed ARI: {'mean': 0.49121, 'median': 0.49987, 'min': 0.40966, 'max': 0.52826, 'std': 0.03567}
- seed NMI: {'mean': 0.64803, 'median': 0.65165, 'min': 0.59776, 'max': 0.68277, 'std': 0.02297}
- resampling ARI full: {'mean': 0.49958, 'median': 0.49772, 'min': 0.46684, 'max': 0.52556, 'std': 0.02108}
- refit cosine silhouette: 0.052967
- refit Davies–Bouldin: 3.705765
- refit Calinski–Harabasz: 56.539694
- original model label agreement: {'original_clusters': 18, 'adjusted_rand_original_vs_refit': 0.38483, 'nmi_original_vs_refit': 0.55257}
- exclusion sensitivity: {'clean_rows': 3648, 'excluded_or_textless_rows': 8, 'ari_full_vs_clean_fit_on_retained': 0.5882, 'nmi_full_vs_clean_fit_on_retained': 0.69499}

### k = 25
- seed ARI: {'mean': 0.51014, 'median': 0.5132, 'min': 0.45415, 'max': 0.57159, 'std': 0.03116}
- seed NMI: {'mean': 0.67925, 'median': 0.67548, 'min': 0.65068, 'max': 0.722, 'std': 0.0195}
- resampling ARI full: {'mean': 0.48254, 'median': 0.48263, 'min': 0.45366, 'max': 0.50659, 'std': 0.01877}
- refit cosine silhouette: 0.051934
- refit Davies–Bouldin: 3.581343
- refit Calinski–Harabasz: 45.823232
- original model label agreement: {'original_clusters': 25, 'adjusted_rand_original_vs_refit': 0.32883, 'nmi_original_vs_refit': 0.53999}
- exclusion sensitivity: {'clean_rows': 3648, 'excluded_or_textless_rows': 8, 'ari_full_vs_clean_fit_on_retained': 0.50951, 'nmi_full_vs_clean_fit_on_retained': 0.68725}

## Limits
- The embedding-array/document alignment is inferred from matching stage order and Parquet ID alignment, not independently cryptographically proven.
- Labels of alternative KMeans partitions are arbitrary; ARI/NMI are permutation invariant.
- Strong seed stability does not prove semantically distinct or policy-relevant clusters.
- Results depend on raw/L2 embedding setting; compare original code before treating refit as identical to manuscript.
- Excluded/textless sensitivity removes records flagged by original extraction metadata, not by newly performed human eligibility screening.
