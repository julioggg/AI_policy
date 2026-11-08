# Phase 23 — Human adjudicated screening and stratified diagnostics

Status: completed_human_screening_adjudication_aggregate_QA_pending

## Completeness
{
  "relevance": {
    "filled": 316,
    "total": 316
  },
  "discipline": {
    "filled": 316,
    "total": 316
  },
  "policy": {
    "filled": 316,
    "total": 316
  },
  "reason": {
    "filled": 316,
    "total": 316
  }
}

## Input integrity
{
  "original_template_unchanged": true,
  "reviewer_source_A_B_unchanged": true,
  "sample_and_strata_keys_verified_privately": true,
  "counts": {
    "relevance": 89,
    "discipline": 218,
    "policy": 183,
    "unique": 316,
    "original_no_disagreement": 52
  }
}

## Public aggregate results only
{
  "human_consensus_source": {
    "adjudicated": 316,
    "unanimous_retained": 52
  },
  "per_stratum_descriptive_counts": {
    "screen_include_core": {
      "n": 120,
      "sampling_population_n": 9264,
      "scope": "final_AI_screening_stratum",
      "relevance_counts": {
        "0": 13,
        "1": 59,
        "2": 41,
        "3": 5,
        "9": 2
      },
      "discipline_counts": {
        "engineering": 9,
        "general_he": 52,
        "health_sciences": 19,
        "ssh": 31,
        "uncertain": 9
      },
      "policy_dimension_counts": {
        "ai_literacy_training": 8,
        "assessment": 10,
        "equity_access": 5,
        "ethics_integrity": 16,
        "general_policy": 5,
        "governance_policy": 12,
        "not_applicable": 13,
        "privacy_security": 1,
        "research_scholarship": 4,
        "teaching_learning": 45,
        "uncertain": 1
      },
      "any_AI_higher_education_1plus_count": 105,
      "policy_at_least_indirect_2plus_count": 46,
      "direct_policy_3_count": 5,
      "unresolved_9_count": 2
    },
    "screen_include_policy": {
      "n": 80,
      "sampling_population_n": 899,
      "scope": "final_AI_screening_stratum",
      "relevance_counts": {
        "0": 9,
        "1": 59,
        "2": 10,
        "3": 0,
        "9": 2
      },
      "discipline_counts": {
        "engineering": 12,
        "general_he": 33,
        "health_sciences": 7,
        "ssh": 26,
        "uncertain": 2
      },
      "policy_dimension_counts": {
        "ai_literacy_training": 1,
        "assessment": 1,
        "equity_access": 2,
        "ethics_integrity": 6,
        "general_policy": 1,
        "governance_policy": 4,
        "not_applicable": 9,
        "privacy_security": 1,
        "research_scholarship": 2,
        "teaching_learning": 53,
        "uncertain": 0
      },
      "any_AI_higher_education_1plus_count": 69,
      "policy_at_least_indirect_2plus_count": 10,
      "direct_policy_3_count": 0,
      "unresolved_9_count": 2
    },
    "screen_include_context": {
      "n": 40,
      "sampling_population_n": 102,
      "scope": "final_AI_screening_stratum",
      "relevance_counts": {
        "0": 29,
        "1": 2,
        "2": 6,
        "3": 0,
        "9": 3
      },
      "discipline_counts": {
        "engineering": 4,
        "general_he": 8,
        "health_sciences": 12,
        "ssh": 7,
        "uncertain": 9
      },
      "policy_dimension_counts": {
        "ai_literacy_training": 1,
        "assessment": 0,
        "equity_access": 1,
        "ethics_integrity": 2,
        "general_policy": 1,
        "governance_policy": 1,
        "not_applicable": 29,
        "privacy_security": 1,
        "research_scholarship": 0,
        "teaching_learning": 4,
        "uncertain": 0
      },
      "any_AI_higher_education_1plus_count": 8,
      "policy_at_least_indirect_2plus_count": 6,
      "direct_policy_3_count": 0,
      "unresolved_9_count": 3
    },
    "screen_exclude": {
      "n": 18,
      "sampling_population_n": 18,
      "scope": "final_AI_screening_stratum",
      "relevance_counts": {
        "0": 18,
        "1": 0,
        "2": 0,
        "3": 0,
        "9": 0
      },
      "discipline_counts": {
        "engineering": 0,
        "general_he": 0,
        "health_sciences": 18,
        "ssh": 0,
        "uncertain": 0
      },
      "policy_dimension_counts": {
        "ai_literacy_training": 0,
        "assessment": 0,
        "equity_access": 0,
        "ethics_integrity": 0,
        "general_policy": 0,
        "governance_policy": 0,
        "not_applicable": 18,
        "privacy_security": 0,
        "research_scholarship": 0,
        "teaching_learning": 0,
        "uncertain": 0
      },
      "any_AI_higher_education_1plus_count": 0,
      "policy_at_least_indirect_2plus_count": 0,
      "direct_policy_3_count": 0,
      "unresolved_9_count": 0
    },
    "q1_not_article_ready": {
      "n": 80,
      "sampling_population_n": 11393,
      "scope": "earlier_bibliographic_filter_exclusion_NOT_AI_classifier_negative",
      "relevance_counts": {
        "0": 37,
        "1": 27,
        "2": 11,
        "3": 1,
        "9": 4
      },
      "discipline_counts": {
        "engineering": 15,
        "general_he": 45,
        "health_sciences": 5,
        "ssh": 7,
        "uncertain": 8
      },
      "policy_dimension_counts": {
        "ai_literacy_training": 4,
        "assessment": 2,
        "equity_access": 2,
        "ethics_integrity": 3,
        "general_policy": 2,
        "governance_policy": 7,
        "not_applicable": 37,
        "privacy_security": 2,
        "research_scholarship": 0,
        "teaching_learning": 18,
        "uncertain": 3
      },
      "any_AI_higher_education_1plus_count": 39,
      "policy_at_least_indirect_2plus_count": 12,
      "direct_policy_3_count": 1,
      "unresolved_9_count": 4
    },
    "core_not_q1": {
      "n": 30,
      "sampling_population_n": 848,
      "scope": "earlier_bibliographic_filter_exclusion_NOT_AI_classifier_negative",
      "relevance_counts": {
        "0": 17,
        "1": 10,
        "2": 1,
        "3": 0,
        "9": 2
      },
      "discipline_counts": {
        "engineering": 2,
        "general_he": 9,
        "health_sciences": 2,
        "ssh": 9,
        "uncertain": 8
      },
      "policy_dimension_counts": {
        "ai_literacy_training": 1,
        "assessment": 1,
        "equity_access": 0,
        "ethics_integrity": 0,
        "general_policy": 1,
        "governance_policy": 1,
        "not_applicable": 17,
        "privacy_security": 0,
        "research_scholarship": 0,
        "teaching_learning": 7,
        "uncertain": 2
      },
      "any_AI_higher_education_1plus_count": 11,
      "policy_at_least_indirect_2plus_count": 1,
      "direct_policy_3_count": 0,
      "unresolved_9_count": 2
    }
  },
  "weighted_four_screening_strata": {
    "status": "conditional_design_based_descriptive_estimate_NOT_classifier_accuracy",
    "target_final_screened_population_N": 10283,
    "assumptions": [
      "The four final AI-screening strata are disjoint and exhaustive over 10,283 screened records.",
      "The Phase05 samples were simple random samples without replacement within each stratum.",
      "Consensus reviewer codes measure title/abstract relevance, not an independent full-text truth standard.",
      "Unresolved 9 is a separate response class in the denominator; confidence intervals are approximate normal-design bounds, not formal claims of classifier performance.",
      "The earlier 11,393 q1_not_article_ready and 848 core_not_q1 records are NOT included in this screen-stage estimator and cannot be treated as machine negatives."
    ],
    "class_prevalence": {
      "outside_scope_0": {
        "estimate": 0.116375,
        "approx_design_se": 0.025679,
        "approx_normal_95_ci_clipped": [
          0.066045,
          0.166706
        ],
        "denominator": "10,283 final-screening-pool records, including uncertain cases",
        "components": {
          "screen_include_core": {
            "sample_n": 120,
            "population_n": 9264,
            "observed_sample_cases": 13
          },
          "screen_include_policy": {
            "sample_n": 80,
            "population_n": 899,
            "observed_sample_cases": 9
          },
          "screen_include_context": {
            "sample_n": 40,
            "population_n": 102,
            "observed_sample_cases": 29
          },
          "screen_exclude": {
            "sample_n": 18,
            "population_n": 18,
            "observed_sample_cases": 18
          }
        }
      },
      "AI_education_non_policy_1": {
        "estimate": 0.507917,
        "approx_design_se": 0.041227,
        "approx_normal_95_ci_clipped": [
          0.427112,
          0.588723
        ],
        "denominator": "10,283 final-screening-pool records, including uncertain cases",
        "components": {
          "screen_include_core": {
            "sample_n": 120,
            "population_n": 9264,
            "observed_sample_cases": 59
          },
          "screen_include_policy": {
            "sample_n": 80,
            "population_n": 899,
            "observed_sample_cases": 59
          },
          "screen_include_context": {
            "sample_n": 40,
            "population_n": 102,
            "observed_sample_cases": 2
          },
          "screen_exclude": {
            "sample_n": 18,
            "population_n": 18,
            "observed_sample_cases": 0
          }
        }
      },
      "policy_at_least_indirect_2plus": {
        "estimate": 0.357763,
        "approx_design_se": 0.040015,
        "approx_normal_95_ci_clipped": [
          0.279333,
          0.436193
        ],
        "denominator": "10,283 final-screening-pool records, including uncertain cases",
        "components": {
          "screen_include_core": {
            "sample_n": 120,
            "population_n": 9264,
            "observed_sample_cases": 46
          },
          "screen_include_policy": {
            "sample_n": 80,
            "population_n": 899,
            "observed_sample_cases": 10
          },
          "screen_include_context": {
            "sample_n": 40,
            "population_n": 102,
            "observed_sample_cases": 6
          },
          "screen_exclude": {
            "sample_n": 18,
            "population_n": 18,
            "observed_sample_cases": 0
          }
        }
      },
      "direct_policy_3": {
        "estimate": 0.037538,
        "approx_design_se": 0.016396,
        "approx_normal_95_ci_clipped": [
          0.005402,
          0.069673
        ],
        "denominator": "10,283 final-screening-pool records, including uncertain cases",
        "components": {
          "screen_include_core": {
            "sample_n": 120,
            "population_n": 9264,
            "observed_sample_cases": 5
          },
          "screen_include_policy": {
            "sample_n": 80,
            "population_n": 899,
            "observed_sample_cases": 0
          },
          "screen_include_context": {
            "sample_n": 40,
            "population_n": 102,
            "observed_sample_cases": 0
          },
          "screen_exclude": {
            "sample_n": 18,
            "population_n": 18,
            "observed_sample_cases": 0
          }
        }
      },
      "uncertain_9": {
        "estimate": 0.017945,
        "approx_design_se": 0.010611,
        "approx_normal_95_ci_clipped": [
          0,
          0.038742
        ],
        "denominator": "10,283 final-screening-pool records, including uncertain cases",
        "components": {
          "screen_include_core": {
            "sample_n": 120,
            "population_n": 9264,
            "observed_sample_cases": 2
          },
          "screen_include_policy": {
            "sample_n": 80,
            "population_n": 899,
            "observed_sample_cases": 2
          },
          "screen_include_context": {
            "sample_n": 40,
            "population_n": 102,
            "observed_sample_cases": 3
          },
          "screen_exclude": {
            "sample_n": 18,
            "population_n": 18,
            "observed_sample_cases": 0
          }
        }
      }
    }
  },
  "adjudication_quality_diagnostics": {
    "conflicting_dimension_choice": {
      "relevance": {
        "conflicting_cases": 89,
        "adjudication_matches_A": 18,
        "adjudication_matches_B": 71,
        "adjudication_matches_neither": 0
      },
      "discipline": {
        "conflicting_cases": 218,
        "adjudication_matches_A": 6,
        "adjudication_matches_B": 212,
        "adjudication_matches_neither": 0
      },
      "policy": {
        "conflicting_cases": 183,
        "adjudication_matches_A": 12,
        "adjudication_matches_B": 165,
        "adjudication_matches_neither": 6
      }
    },
    "adjudicator_justification_unique_count": 153,
    "adjudicator_justifications_using_common_relevance_template_n": 226,
    "unresolved_relevance_9_count": 13,
    "outside_AI_HE_0_with_non_NA_policy_dimension": 0,
    "cautions": [
      "Large directional preference for reviewer B in discipline; independent protocol/justification spot-check recommended",
      "Large directional preference for reviewer B in policy; independent protocol/justification spot-check recommended"
    ],
    "interpretation": "Quality checks do not establish procedural independence, correctness or intentional bias."
  },
  "classifier_performance_status": "NOT_COMPUTED_no_silent_mapping_of_multi_class_screen_to_binary_truth"
}

## Limitations
- The adjudicator saw original A/B ratings; this reconciled result is NOT a third independent blinded evaluation.
- Descriptive human consensus on title/abstract does not constitute a definitive full-text inclusion truth standard.
- Sampling is intentionally stratified; unweighted pooled accuracy, precision/recall, or prevalence would be misleading.
- Early q1_not_article_ready/core_not_q1 filter exclusions are NOT machine classifier negatives.
- Unresolved relevance score 9 must not be silently forced into any binary class.
- Preferential selection of one reviewer may warrant independent quality review of decisions, rubric compliance and evidence before publication.
- No private identifiers, text, individual ratings, consensus reasons or per-item machine labels are published.
