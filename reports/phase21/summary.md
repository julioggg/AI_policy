# Phase 21 — Human screening agreement, before adjudication

Status: complete_independent_ratings_not_yet_adjudicated
UTC: 2026-11-08T02:36:01.420490+00:00

## Rating completeness
{
  "a": {
    "relevance_code": {
      "filled": 368,
      "total": 368
    },
    "discipline_code": {
      "filled": 368,
      "total": 368
    },
    "primary_policy_code": {
      "filled": 368,
      "total": 368
    },
    "reason": {
      "filled": 368,
      "total": 368
    }
  },
  "b": {
    "relevance_code": {
      "filled": 368,
      "total": 368
    },
    "discipline_code": {
      "filled": 368,
      "total": 368
    },
    "primary_policy_code": {
      "filled": 368,
      "total": 368
    },
    "reason": {
      "filled": 368,
      "total": 368
    }
  }
}

## Agreement and strata (aggregate only)
{
  "overall_inter_rater": {
    "relevance": {
      "rater_a": {
        "0": 111,
        "1": 201,
        "2": 37,
        "3": 10,
        "9": 9
      },
      "rater_b": {
        "0": 122,
        "1": 159,
        "2": 73,
        "3": 6,
        "9": 8
      },
      "full_sample_exact_agreement": 0.75815,
      "all_including_uncertain_disagreements": 89,
      "ordinal_0_to_3_unweighted": {
        "paired_evaluable": 351,
        "not_jointly_evaluable": 17,
        "agreement": 0.79487,
        "disagreements": 72,
        "cohen_kappa": 0.67334
      },
      "ordinal_0_to_3_quadratic_weighted": {
        "paired_evaluable": 351,
        "not_jointly_evaluable": 17,
        "agreement": 0.79487,
        "disagreements": 72,
        "cohen_kappa": 0.75365
      },
      "any_uncertain_9": 17
    },
    "discipline": {
      "rater_a": {
        "ssh": 38,
        "engineering": 26,
        "health_sciences": 80,
        "general_he": 104,
        "uncertain": 120
      },
      "rater_b": {
        "ssh": 80,
        "engineering": 40,
        "health_sciences": 63,
        "general_he": 152,
        "uncertain": 33
      },
      "full_sample_exact_agreement": 0.40761,
      "all_including_uncertain_disagreements": 218,
      "nominal_kappa_with_uncertain_as_category": {
        "paired_evaluable": 368,
        "not_jointly_evaluable": 0,
        "agreement": 0.40761,
        "disagreements": 218,
        "cohen_kappa": 0.24698
      }
    },
    "primary_policy_dimension": {
      "rater_a": {
        "teaching_learning": 43,
        "assessment": 69,
        "ethics_integrity": 39,
        "governance_policy": 38,
        "research_scholarship": 28,
        "ai_literacy_training": 14,
        "equity_access": 9,
        "privacy_security": 7,
        "general_policy": 1,
        "not_applicable": 120,
        "uncertain": 0
      },
      "rater_b": {
        "teaching_learning": 134,
        "assessment": 13,
        "ethics_integrity": 28,
        "governance_policy": 21,
        "research_scholarship": 4,
        "ai_literacy_training": 16,
        "equity_access": 9,
        "privacy_security": 5,
        "general_policy": 11,
        "not_applicable": 122,
        "uncertain": 5
      },
      "full_sample_exact_agreement": 0.50272,
      "all_including_uncertain_disagreements": 183,
      "nominal_kappa_with_uncertain_as_category": {
        "paired_evaluable": 368,
        "not_jointly_evaluable": 0,
        "agreement": 0.50272,
        "disagreements": 183,
        "cohen_kappa": 0.39749
      }
    }
  },
  "stratified_review_summary": {
    "screen_include_core": {
      "sample_n": 120,
      "relevance_distribution": {
        "a": {
          "0": 11,
          "1": 80,
          "2": 19,
          "3": 9,
          "9": 1
        },
        "b": {
          "0": 12,
          "1": 60,
          "2": 42,
          "3": 5,
          "9": 1
        }
      },
      "relevance_agreement": {
        "paired_evaluable": 118,
        "not_jointly_evaluable": 2,
        "agreement": 0.72034,
        "disagreements": 33,
        "cohen_kappa": 0.70582
      },
      "relevance_exact_with_9": 0.70833,
      "discipline_agreement": {
        "paired_evaluable": 120,
        "not_jointly_evaluable": 0,
        "agreement": 0.525,
        "disagreements": 57,
        "cohen_kappa": 0.36182
      },
      "policy_dimension_agreement": {
        "paired_evaluable": 120,
        "not_jointly_evaluable": 0,
        "agreement": 0.38333,
        "disagreements": 74,
        "cohen_kappa": 0.30222
      },
      "scope": "final_AI_screening_stratum"
    },
    "screen_include_policy": {
      "sample_n": 80,
      "relevance_distribution": {
        "a": {
          "0": 8,
          "1": 65,
          "2": 4,
          "3": 0,
          "9": 3
        },
        "b": {
          "0": 10,
          "1": 58,
          "2": 12,
          "3": 0,
          "9": 0
        }
      },
      "relevance_agreement": {
        "paired_evaluable": 77,
        "not_jointly_evaluable": 3,
        "agreement": 0.87013,
        "disagreements": 10,
        "cohen_kappa": 0.6875
      },
      "relevance_exact_with_9": 0.8375,
      "discipline_agreement": {
        "paired_evaluable": 80,
        "not_jointly_evaluable": 0,
        "agreement": 0.475,
        "disagreements": 42,
        "cohen_kappa": 0.31498
      },
      "policy_dimension_agreement": {
        "paired_evaluable": 80,
        "not_jointly_evaluable": 0,
        "agreement": 0.45,
        "disagreements": 44,
        "cohen_kappa": 0.2967
      },
      "scope": "final_AI_screening_stratum"
    },
    "screen_include_context": {
      "sample_n": 40,
      "relevance_distribution": {
        "a": {
          "0": 27,
          "1": 8,
          "2": 5,
          "3": 0,
          "9": 0
        },
        "b": {
          "0": 29,
          "1": 2,
          "2": 6,
          "3": 0,
          "9": 3
        }
      },
      "relevance_agreement": {
        "paired_evaluable": 37,
        "not_jointly_evaluable": 3,
        "agreement": 0.83784,
        "disagreements": 6,
        "cohen_kappa": 0.67919
      },
      "relevance_exact_with_9": 0.775,
      "discipline_agreement": {
        "paired_evaluable": 40,
        "not_jointly_evaluable": 0,
        "agreement": 0.375,
        "disagreements": 25,
        "cohen_kappa": 0.19936
      },
      "policy_dimension_agreement": {
        "paired_evaluable": 40,
        "not_jointly_evaluable": 0,
        "agreement": 0.775,
        "disagreements": 9,
        "cohen_kappa": 0.54603
      },
      "scope": "final_AI_screening_stratum"
    },
    "screen_exclude": {
      "sample_n": 18,
      "relevance_distribution": {
        "a": {
          "0": 18,
          "1": 0,
          "2": 0,
          "3": 0,
          "9": 0
        },
        "b": {
          "0": 18,
          "1": 0,
          "2": 0,
          "3": 0,
          "9": 0
        }
      },
      "relevance_agreement": {
        "paired_evaluable": 18,
        "not_jointly_evaluable": 0,
        "agreement": 1.0,
        "disagreements": 0,
        "cohen_kappa": null
      },
      "relevance_exact_with_9": 1.0,
      "discipline_agreement": {
        "paired_evaluable": 18,
        "not_jointly_evaluable": 0,
        "agreement": 0.0,
        "disagreements": 18,
        "cohen_kappa": 0.0
      },
      "policy_dimension_agreement": {
        "paired_evaluable": 18,
        "not_jointly_evaluable": 0,
        "agreement": 1.0,
        "disagreements": 0,
        "cohen_kappa": null
      },
      "scope": "final_AI_screening_stratum"
    },
    "q1_not_article_ready": {
      "sample_n": 80,
      "relevance_distribution": {
        "a": {
          "0": 32,
          "1": 35,
          "2": 8,
          "3": 1,
          "9": 4
        },
        "b": {
          "0": 36,
          "1": 28,
          "2": 12,
          "3": 1,
          "9": 3
        }
      },
      "relevance_agreement": {
        "paired_evaluable": 73,
        "not_jointly_evaluable": 7,
        "agreement": 0.75342,
        "disagreements": 18,
        "cohen_kappa": 0.62856
      },
      "relevance_exact_with_9": 0.6875,
      "discipline_agreement": {
        "paired_evaluable": 80,
        "not_jointly_evaluable": 0,
        "agreement": 0.3125,
        "disagreements": 55,
        "cohen_kappa": 0.11272
      },
      "policy_dimension_agreement": {
        "paired_evaluable": 80,
        "not_jointly_evaluable": 0,
        "agreement": 0.4625,
        "disagreements": 43,
        "cohen_kappa": 0.29953
      },
      "scope": "previous_bibliographic_filter_exclusion_NOT_AI_classifier_negative"
    },
    "core_not_q1": {
      "sample_n": 30,
      "relevance_distribution": {
        "a": {
          "0": 15,
          "1": 13,
          "2": 1,
          "3": 0,
          "9": 1
        },
        "b": {
          "0": 17,
          "1": 11,
          "2": 1,
          "3": 0,
          "9": 1
        }
      },
      "relevance_agreement": {
        "paired_evaluable": 28,
        "not_jointly_evaluable": 2,
        "agreement": 0.82143,
        "disagreements": 5,
        "cohen_kappa": 0.55556
      },
      "relevance_exact_with_9": 0.76667,
      "discipline_agreement": {
        "paired_evaluable": 30,
        "not_jointly_evaluable": 0,
        "agreement": 0.3,
        "disagreements": 21,
        "cohen_kappa": 0.11517
      },
      "policy_dimension_agreement": {
        "paired_evaluable": 30,
        "not_jointly_evaluable": 0,
        "agreement": 0.56667,
        "disagreements": 13,
        "cohen_kappa": 0.33898
      },
      "scope": "previous_bibliographic_filter_exclusion_NOT_AI_classifier_negative"
    }
  },
  "flagged_for_human_adjudication": {
    "any_relevance_disagreement": 89,
    "any_discipline_disagreement": 218,
    "any_policy_dimension_disagreement": 183,
    "unique_records_disagreeing_in_one_or_more_fields": 316
  },
  "classifier_accuracy_status": "NO_GOLD_STANDARD_YET_independent_human_ratings_require_adjudication"
}

## Limits
- The two screening forms are computationally comparable, but independence of human judgment is a procedural assertion that code cannot verify.
- Agreement between human coders does not establish an external gold standard, an unbiased classifier recall, precision, or screening validity.
- Ordinal relevance κ excludes 9=uncertain. All-record exact agreement includes 9 as a scored category and is shown separately.
- Discipline and policy dimension are nominal with uncertain treated as a category; their kappa must not be compared numerically to ordinal weighted relevance kappa as if identical.
- The 368-record sample deliberately oversamples minority classes and early-filter exclusions. Aggregate per-stratum distributions are NOT population prevalences.
- The Q1/refinement and core-to-Q1 exclusion strata are bibliographic-filter exclusions, NOT final AI-screening negatives.
- Machine labels are excluded from this independent agreement report. A subsequent human adjudication should precede any model-vs-human validity analysis.
- Assessing title/abstract alone is not a full-text relevance or risk-of-bias judgment.
- Only counts and agreement are published; raw titles, abstracts, comments, decisions linked to records, identifiers and private sampling keys remain on CEDIA.
