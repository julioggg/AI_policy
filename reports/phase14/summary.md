# Phase 14 — Comparative full-corpus KMeans stability

UTC: 2026-11-07T23:33:48.150329+00:00

## Matched population
{
  "fulltext_rows": 3656,
  "explicit_acceptances": 3644,
  "body_usable": 3629,
  "body_unusable": 15,
  "private_input_fingerprint_verified": true,
  "legacy_fulltext_parquet_alignment_verified": true,
  "model": "sentence-transformers/all-MiniLM-L6-v2",
  "dimension": 384,
  "comparison_uses_same_document_population": true
}

## Model settings
{
  "modalities": [
    "bibliographic",
    "legacy_fulltext",
    "body_chunks",
    "hybrid_equal"
  ],
  "k_values": [
    12,
    18,
    25
  ],
  "seeds": [
    42,
    55,
    68
  ],
  "n_init": 10,
  "max_iter": 300,
  "subsamples": 3,
  "subsample_fraction": 0.8,
  "cosine_silhouette_common_fixed_sample": 1200,
  "all_inputs_l2_normalized": true,
  "same_publications_for_all_modalities": true
}

## k = 12

### bibliographic
- cosine silhouette: 0.063372
- stability across random seeds ARI: {'mean': 0.60423, 'median': 0.5974, 'min': 0.56609, 'max': 0.64922, 'std': 0.03428}
- 80% subset ARI vs reference: {'mean': 0.58005, 'median': 0.5642, 'min': 0.47486, 'max': 0.7011, 'std': 0.09304}
- cluster sizes: min=111, median=288.5, <=20=0
- weak-label AMI: {'policy_dimension_ami_weak_labels': 0.10026, 'disciplinary_area_ami_weak_labels': 0.09961}

### legacy_fulltext
- cosine silhouette: 0.052512
- stability across random seeds ARI: {'mean': 0.5868, 'median': 0.51856, 'min': 0.51373, 'max': 0.72811, 'std': 0.09994}
- 80% subset ARI vs reference: {'mean': 0.6176, 'median': 0.61748, 'min': 0.59816, 'max': 0.63717, 'std': 0.01593}
- cluster sizes: min=174, median=299.5, <=20=0
- weak-label AMI: {'policy_dimension_ami_weak_labels': 0.08772, 'disciplinary_area_ami_weak_labels': 0.09906}

### body_chunks
- cosine silhouette: 0.116005
- stability across random seeds ARI: {'mean': 0.76291, 'median': 0.69458, 'min': 0.69222, 'max': 0.90194, 'std': 0.09831}
- 80% subset ARI vs reference: {'mean': 0.63463, 'median': 0.5993, 'min': 0.59474, 'max': 0.70985, 'std': 0.05322}
- cluster sizes: min=47, median=302.0, <=20=0
- weak-label AMI: {'policy_dimension_ami_weak_labels': 0.0514, 'disciplinary_area_ami_weak_labels': 0.08764}

### hybrid_equal
- cosine silhouette: 0.08361
- stability across random seeds ARI: {'mean': 0.54718, 'median': 0.51821, 'min': 0.44882, 'max': 0.6745, 'std': 0.09439}
- 80% subset ARI vs reference: {'mean': 0.50393, 'median': 0.54238, 'min': 0.41621, 'max': 0.5532, 'std': 0.06219}
- cluster sizes: min=63, median=278.0, <=20=0
- weak-label AMI: {'policy_dimension_ami_weak_labels': 0.08143, 'disciplinary_area_ami_weak_labels': 0.10554}

### Between representations
{'bibliographic__legacy_fulltext': {'ari': 0.60759, 'nmi': 0.68675}, 'bibliographic__body_chunks': {'ari': 0.19363, 'nmi': 0.30895}, 'bibliographic__hybrid_equal': {'ari': 0.34866, 'nmi': 0.50108}, 'legacy_fulltext__body_chunks': {'ari': 0.2096, 'nmi': 0.31243}, 'legacy_fulltext__hybrid_equal': {'ari': 0.31725, 'nmi': 0.46005}, 'body_chunks__hybrid_equal': {'ari': 0.41743, 'nmi': 0.50613}}

## k = 18

### bibliographic
- cosine silhouette: 0.051615
- stability across random seeds ARI: {'mean': 0.51932, 'median': 0.5411, 'min': 0.47484, 'max': 0.54201, 'std': 0.03145}
- 80% subset ARI vs reference: {'mean': 0.52092, 'median': 0.533, 'min': 0.46658, 'max': 0.56318, 'std': 0.04035}
- cluster sizes: min=99, median=192.0, <=20=0
- weak-label AMI: {'policy_dimension_ami_weak_labels': 0.09991, 'disciplinary_area_ami_weak_labels': 0.08774}

### legacy_fulltext
- cosine silhouette: 0.051202
- stability across random seeds ARI: {'mean': 0.48533, 'median': 0.49281, 'min': 0.46635, 'max': 0.49685, 'std': 0.01352}
- 80% subset ARI vs reference: {'mean': 0.473, 'median': 0.50244, 'min': 0.39563, 'max': 0.52093, 'std': 0.05523}
- cluster sizes: min=117, median=213.0, <=20=0
- weak-label AMI: {'policy_dimension_ami_weak_labels': 0.10096, 'disciplinary_area_ami_weak_labels': 0.09547}

### body_chunks
- cosine silhouette: 0.100827
- stability across random seeds ARI: {'mean': 0.54393, 'median': 0.54807, 'min': 0.53217, 'max': 0.55154, 'std': 0.00844}
- 80% subset ARI vs reference: {'mean': 0.50339, 'median': 0.4932, 'min': 0.48332, 'max': 0.53366, 'std': 0.02178}
- cluster sizes: min=44, median=186.0, <=20=0
- weak-label AMI: {'policy_dimension_ami_weak_labels': 0.07078, 'disciplinary_area_ami_weak_labels': 0.09206}

### hybrid_equal
- cosine silhouette: 0.076961
- stability across random seeds ARI: {'mean': 0.64751, 'median': 0.63437, 'min': 0.54653, 'max': 0.76164, 'std': 0.08831}
- 80% subset ARI vs reference: {'mean': 0.60069, 'median': 0.60312, 'min': 0.59241, 'max': 0.60654, 'std': 0.00602}
- cluster sizes: min=63, median=195.0, <=20=0
- weak-label AMI: {'policy_dimension_ami_weak_labels': 0.09034, 'disciplinary_area_ami_weak_labels': 0.09144}

### Between representations
{'bibliographic__legacy_fulltext': {'ari': 0.49418, 'nmi': 0.63266}, 'bibliographic__body_chunks': {'ari': 0.22722, 'nmi': 0.37129}, 'bibliographic__hybrid_equal': {'ari': 0.38542, 'nmi': 0.53727}, 'legacy_fulltext__body_chunks': {'ari': 0.21793, 'nmi': 0.34821}, 'legacy_fulltext__hybrid_equal': {'ari': 0.38085, 'nmi': 0.50822}, 'body_chunks__hybrid_equal': {'ari': 0.38416, 'nmi': 0.54208}}

## k = 25

### bibliographic
- cosine silhouette: 0.046123
- stability across random seeds ARI: {'mean': 0.52488, 'median': 0.52758, 'min': 0.51275, 'max': 0.53431, 'std': 0.00901}
- 80% subset ARI vs reference: {'mean': 0.48484, 'median': 0.50462, 'min': 0.4336, 'max': 0.5163, 'std': 0.03654}
- cluster sizes: min=71, median=140.0, <=20=0
- weak-label AMI: {'policy_dimension_ami_weak_labels': 0.09799, 'disciplinary_area_ami_weak_labels': 0.08884}

### legacy_fulltext
- cosine silhouette: 0.044727
- stability across random seeds ARI: {'mean': 0.55287, 'median': 0.56381, 'min': 0.51352, 'max': 0.58129, 'std': 0.02873}
- 80% subset ARI vs reference: {'mean': 0.4853, 'median': 0.49204, 'min': 0.4612, 'max': 0.50265, 'std': 0.01758}
- cluster sizes: min=64, median=143.0, <=20=0
- weak-label AMI: {'policy_dimension_ami_weak_labels': 0.09655, 'disciplinary_area_ami_weak_labels': 0.08728}

### body_chunks
- cosine silhouette: 0.084329
- stability across random seeds ARI: {'mean': 0.5429, 'median': 0.52448, 'min': 0.5019, 'max': 0.60232, 'std': 0.04302}
- 80% subset ARI vs reference: {'mean': 0.49775, 'median': 0.48863, 'min': 0.4693, 'max': 0.53531, 'std': 0.02771}
- cluster sizes: min=15, median=131.0, <=20=1
- weak-label AMI: {'policy_dimension_ami_weak_labels': 0.07546, 'disciplinary_area_ami_weak_labels': 0.07876}

### hybrid_equal
- cosine silhouette: 0.081086
- stability across random seeds ARI: {'mean': 0.67951, 'median': 0.68678, 'min': 0.64466, 'max': 0.70711, 'std': 0.02601}
- 80% subset ARI vs reference: {'mean': 0.64432, 'median': 0.63192, 'min': 0.61235, 'max': 0.68869, 'std': 0.03238}
- cluster sizes: min=28, median=137.0, <=20=0
- weak-label AMI: {'policy_dimension_ami_weak_labels': 0.08624, 'disciplinary_area_ami_weak_labels': 0.08794}

### Between representations
{'bibliographic__legacy_fulltext': {'ari': 0.53279, 'nmi': 0.70371}, 'bibliographic__body_chunks': {'ari': 0.20181, 'nmi': 0.38428}, 'bibliographic__hybrid_equal': {'ari': 0.35933, 'nmi': 0.54406}, 'legacy_fulltext__body_chunks': {'ari': 0.22259, 'nmi': 0.38965}, 'legacy_fulltext__hybrid_equal': {'ari': 0.38631, 'nmi': 0.5403}, 'body_chunks__hybrid_equal': {'ari': 0.40201, 'nmi': 0.58987}}

## Interpretation limits
- Silhouette is geometric separation, NOT topic coherence, construct validity, or policy usefulness.
- The policy_dimension and disciplinary_area labels are algorithmic metadata, not independent human ground truth.
- Subsample fits are compared to a seed-42 full-data reference; the ARI is a stability diagnostic, not an accuracy measure.
- k=12/18/25 are pre-existing candidate values; higher silhouette alone does not establish optimal k.
- The 15 records without eligible body chunks are omitted from ALL compared modalities to preserve the paired population.
- Original legacy vectors were obtained through a pipeline subject to severe input token truncation.
- The extracted PDF text is character-capped and body segmentation is approximate; full-document coverage is not demonstrated.
- The document-level assignments and internal cache fingerprint remain private and are not suitable for public GitHub.
- Human adjudication and semantic topic naming remain outstanding, and original manuscript labels are not automatically superseded.
