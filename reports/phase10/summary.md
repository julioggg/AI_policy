# Phase 10 — MiniLM truncation and environment audit

UTC: 2026-11-07T22:11:39.602447+00:00

## Python environment
{'python_version': '3.10.20', 'python_executable_basename': 'python', 'running_inside_singularity': True, 'dependency_availability': {'numpy': {'import_discoverable': True, 'version': '1.26.4'}, 'pandas': {'import_discoverable': True, 'version': '2.3.3'}, 'pyarrow': {'import_discoverable': True, 'version': '24.0.0'}, 'scikit-learn': {'import_discoverable': True, 'version': '1.7.2'}, 'torch': {'import_discoverable': False, 'version': None}, 'transformers': {'import_discoverable': False, 'version': None}, 'sentence-transformers': {'import_discoverable': False, 'version': None}, 'tokenizers': {'import_discoverable': False, 'version': None}}, 'common_virtualenv_candidates': {'.venv': False, 'venv': False, 'ai_policy_he/.venv': True, 'ai_policy_he/venv': False, 'ai_policy_he/env': False, 'ai_policy_he/.conda': False, '.local/share/virtualenvs': False, 'miniconda3': False, 'mambaforge': False, 'anaconda3': False}, 'model_cache_presence': {'hf_hub_model_default_cache': True, 'torch_sentence_transformer_cache': False, 'HF_HOME_is_configured': False, 'SENTENCE_TRANSFORMERS_HOME_is_configured': False, 'HF_HUB_OFFLINE_is_configured': False}}

## Offline tokenizer
{'status': 'offline_tokenizer_not_available', 'exception_type': 'ModuleNotFoundError'}

## Whitespace token prefix audit
{'paired_explicitly_accepted': 3644, 'whitespace_token_prefix_comparison': {'64': {'eligible_pairs_with_at_least_n_words': 3630, 'identical_first_n_words': 3630}, '128': {'eligible_pairs_with_at_least_n_words': 3474, 'identical_first_n_words': 3464}, '256': {'eligible_pairs_with_at_least_n_words': 1171, 'identical_first_n_words': 1158}, '384': {'eligible_pairs_with_at_least_n_words': 219, 'identical_first_n_words': 217}, '512': {'eligible_pairs_with_at_least_n_words': 104, 'identical_first_n_words': 103}, '768': {'eligible_pairs_with_at_least_n_words': 60, 'identical_first_n_words': 53}}, 'source_text_caps': {'full_text_exactly_30003_characters': 2932, 'topic_text_exactly_16000_characters': 1819}, 'caution': 'Word splits are NOT MiniLM WordPiece token counts; actual tokenizer inspection remains required.'}

## Original program source clues
- 03_embeddings_and_clusters.py: [{'line': 41, 'kind': 'call', 'name': 'SentenceTransformer', 'first_arg': '[expression]', 'safe_kwargs': {}}, {'line': 43, 'kind': 'assignment', 'parameter': 'batch_size', 'value': '[expression]'}, {'line': 46, 'kind': 'call', 'name': 'encode', 'first_arg': None, 'safe_kwargs': {'batch_size': '[expression]', 'normalize_embeddings': True}}]
- 12_fulltext_screening_and_extraction.py: [{'line': 102, 'kind': 'slice_limit', 'upper_bound': 8000}, {'line': 129, 'kind': 'call', 'name': 'SentenceTransformer', 'first_arg': 'sentence-transformers/all-MiniLM-L6-v2', 'safe_kwargs': {}}, {'line': 131, 'kind': 'call', 'name': 'encode', 'first_arg': None, 'safe_kwargs': {'batch_size': '[expression]', 'normalize_embeddings': True}}, {'line': 139, 'kind': 'call', 'name': 'encode', 'first_arg': None, 'safe_kwargs': {'normalize_embeddings': True}}, {'line': 140, 'kind': 'call', 'name': 'encode', 'first_arg': None, 'safe_kwargs': {'normalize_embeddings': True}}, {'line': 141, 'kind': 'call', 'name': 'encode', 'first_arg': None, 'safe_kwargs': {'normalize_embeddings': True}}]
- 16_fulltext_topic_modeling_umap_hdbscan.py: [{'line': 59, 'kind': 'call', 'name': 'SentenceTransformer', 'first_arg': 'sentence-transformers/all-MiniLM-L6-v2', 'safe_kwargs': {}}, {'line': 61, 'kind': 'call', 'name': 'encode', 'first_arg': None, 'safe_kwargs': {'batch_size': '[expression]', 'normalize_embeddings': True}}, {'line': 71, 'kind': 'call', 'name': 'UMAP', 'first_arg': None, 'safe_kwargs': {'random_state': 42}}, {'line': 81, 'kind': 'call', 'name': 'HDBSCAN', 'first_arg': None, 'safe_kwargs': {}}]
- 18_fulltext_topic_modeling_kmeans_robust.py: []

## Limitations
- Identical vectors are confirmed by phase09, but identifying truncation requires original tokenizer/model settings.
- The online/offline model availability of the current Python does not rule out other Singularity or virtualenv installations.
- Source-code syntax signals do not establish that a parameter was used in the saved embedding matrices.
- No model downloads, new embeddings, raw texts or source-project modifications were performed.
