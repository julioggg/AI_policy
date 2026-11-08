# Phase27 — Returned methods-panel screening reconciliation audit

Status: completed_panel_reconciliation_reviewed_not_independently_validated

## Source integrity and all four consensus fields
{
  "source_integrity": {
    "returned_workbook_matches_original_sample": true,
    "all_historical_source_text_and_evaluations_unchanged": true,
    "all_original_panel_decision_cells_blank": true,
    "phase25_and_phase26_aggregate_conflicts_reverified": true,
    "phase26_original_mismatch_counts": {
      "relevance": 47,
      "discipline": 58,
      "policy": 71,
      "unique": 80
    }
  },
  "readiness": {
    "relevance": {
      "filled": 80,
      "total": 80
    },
    "discipline": {
      "filled": 80,
      "total": 80
    },
    "policy": {
      "filled": 80,
      "total": 80
    },
    "scientific_justification": {
      "filled": 80,
      "total": 80
    }
  }
}

## Descriptive panel disposition — DOES NOT independently validate previous consensus
{
  "relevance": {
    "records": 80,
    "retained_prior_consensus": 78,
    "changed_prior_consensus": 2,
    "agreement_with_prior_fraction": 0.975,
    "agreement_with_prior_qa_fraction": 0.425,
    "agree_with_prior_QA_cases": 34,
    "final_category_counts": {
      "0": 10,
      "1": 32,
      "2": 19,
      "3": 6,
      "9": 13
    },
    "changes_from_prior": {
      "2_to_1": 2
    },
    "comparison_type": "original independent Phase24 QA ratings compared with nonblinded panel"
  },
  "discipline": {
    "records": 80,
    "retained_prior_consensus": 80,
    "changed_prior_consensus": 0,
    "agreement_with_prior_fraction": 1.0,
    "agreement_with_prior_qa_fraction": 0.275,
    "agree_with_prior_QA_cases": 22,
    "final_category_counts": {
      "engineering": 8,
      "general_he": 35,
      "health_sciences": 8,
      "ssh": 16,
      "uncertain": 13
    },
    "changes_from_prior": {},
    "comparison_type": "original independent Phase24 QA ratings compared with nonblinded panel"
  },
  "policy_posthoc": {
    "records": 80,
    "retained_prior_consensus": 79,
    "changed_prior_consensus": 1,
    "agreement_with_prior_fraction": 0.9875,
    "agreement_with_prior_qa_fraction": 0.1125,
    "agree_with_prior_QA_cases": 9,
    "final_category_counts": {
      "ai_literacy_training": 4,
      "assessment": 2,
      "equity_access": 3,
      "ethics_integrity": 7,
      "general_policy": 6,
      "governance_policy": 10,
      "not_applicable": 10,
      "privacy_security": 1,
      "research_scholarship": 1,
      "teaching_learning": 30,
      "uncertain": 6
    },
    "changes_from_prior": {
      "equity_access_to_teaching_learning": 1
    },
    "comparison_type": "posthoc-normalized policy QA, NOT original blind codebook QA"
  },
  "panel_justification_diagnostics": {
    "filled": 80,
    "distinct_rationale_strings": 79,
    "using_category_prefix_template": 80,
    "residual_uncertain_9_relevance": 13,
    "all_three_dimensions_identical_to_prior_consensus_n": 78,
    "interpretation": "Text-pattern and prior-consensus retention flags are methodological cautions, not proof of correctness, independence, invalidity or fabrication."
  },
  "scientific_stop_rule": {
    "methodological_compatibility_vs_blind_QA": "UNRESOLVED",
    "independent_agreement_not_recalculated_by_nonblinded_panel": true,
    "original_Phase25_80case_QA_remains_independent": true,
    "phase23_population_estimates_automatically_updated": false,
    "policy_codebook_validity_and_rater_training_require_external_documentation": true,
    "next_needed": "Document a panel protocol/coder independence and full-text resolution or independent blinded rescreen on a new probability sample before making validation claims."
  }
}

## Limits
- A panel that saw the prior A/B and consensus decisions cannot be treated as an independent blinded validation round.
- Very high retention of the previous consensus, if seen, requires protocol and case-specific rationales rather than automatic endorsement.
- Original independent Phase24 relevance and discipline ratings retain their status. Later codebook-normalized Phase24 policy was post hoc and must be labelled as such.
- The 80-case panel sample was deliberately risk-enriched and cannot be extrapolated to all 368 or 10,283 corpus records.
- The original Phase23 stratum-weighted estimates are unchanged; this script does not recalculate classifier accuracy, precision or recall.
- The presence of text in rationales is not itself a demonstration that a methods panel met procedural independence or study-quality criteria.
- No raw records, blinded QA IDs, human case justifications, article titles/abstracts or matching keys are released.
