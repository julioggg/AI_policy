# Phase25 — Independent Phase24 QA versus prior human consensus

Status: independent_qa_scored_with_posthoc_policy_normalization

## Agreement, aggregate only
{
  "independent_QA_relevance_vs_prior_human_consensus": {
    "paired_all_including_9": 80,
    "exact_agreement_all_including_9": 0.4125,
    "uncertain_consensus_n": 13,
    "uncertain_qa_n": 0,
    "paired_evaluable_excluding_9": 67,
    "kappa_unweighted": 0.31447,
    "kappa_quadratic": 0.31315
  },
  "independent_QA_discipline_vs_prior_human_consensus": {
    "n": 80,
    "exact_agreement": 0.275,
    "cohen_kappa": 0.13755
  },
  "relevance_distribution": {
    "qa": {
      "1": 32,
      "3": 32,
      "2": 14,
      "0": 2
    },
    "prior_consensus": {
      "1": 30,
      "0": 10,
      "9": 13,
      "2": 21,
      "3": 6
    }
  },
  "consensus_9_selected_for_QA_n": 13,
  "consensus_9_QA_reclassified_as_0_to_3_n": 13,
  "relevance_mismatch_cases": 47,
  "discipline_mismatch_cases": 58,
  "qa_policy_codebook_status": "post_hoc_normalized_mixed_analyst_and_expert",
  "policy_original_QA_labels_outside_rubric_n": 80,
  "post_hoc_normalized_policy_vs_prior_consensus": {
    "n": 80,
    "exact_agreement": 0.1125,
    "cohen_kappa": 0.00647
  },
  "post_hoc_policy_mismatch_cases": 71,
  "post_hoc_policy_distribution": {
    "normalized_qa": {
      "not_applicable": 34,
      "governance_policy": 12,
      "ethics_integrity": 31,
      "assessment": 3
    },
    "prior_consensus": {
      "ai_literacy_training": 4,
      "not_applicable": 10,
      "ethics_integrity": 7,
      "teaching_learning": 29,
      "governance_policy": 10,
      "uncertain": 6,
      "general_policy": 6,
      "research_scholarship": 1,
      "equity_access": 4,
      "privacy_security": 1,
      "assessment": 2
    }
  }
}

## Policy normalization readiness
{
  "normalization_rows": 80,
  "validated_final_codes": 80,
  "pending_ambiguous_or_revised_codes": 0,
  "proposed_semantic_equivalences_n": 59,
  "changes_to_proposed_equivalence_n": 4,
  "post_hoc_normalization_does_not_constitute_independent_QA_policy_scoring": true,
  "status": "complete"
}

## Restrictions
- Independent QA assessor must have been procedurally blind to A/B, prior consensus, model labels and sample stratification; script cannot prove this.
- This 80-item audit was deliberately enriched for uncertain, reviewer-disputed and policy-sensitive cases; any agreement is descriptive for the selected sample only.
- Risk-selected QA disagreement proportions are not unbiased corpus classification accuracy, precision or recall.
- The 80 QA policy labels were originally nonstandard and cannot be treated as codebook-compliant until normalization is complete and reviewed.
- The normalized policy dimension (if completed) mixes transparent analyst equivalence proposals and expert decisions: do not present it as originally independently coded using the official taxonomy.
- The Phase23 original human consensus is not automatically overwritten by the QA review.
- Code 9 is uncertainty and should not be silently counted as an inclusion or exclusion.
- No publication identifier, title/abstract text, reviewer/adjudicator rationale or record-level rating is disclosed.
