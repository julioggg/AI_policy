# Phase35 — Design-weighted title/abstract scope validation

**Status:** design_weighted_title_abstract_AI_screen_vs_PI_attributed_human_reference_NO_fulltext_truth

Target: N=10,283 final screen only; n=1200, 4 disproportionate machine screening strata; reference still has 74 unresolved R9.

## Weighted human relevance by machine screening stratum

{
  "screen_include_core": {
    "0": 1285.38,
    "1": 6936.42,
    "2": 115.8,
    "3": 416.88,
    "9": 509.52
  },
  "screen_include_policy": {
    "0": 127.1,
    "1": 713.0,
    "2": 6.2,
    "3": 6.2,
    "9": 46.5
  },
  "screen_include_context": {
    "0": 69.848,
    "1": 14.413,
    "2": 0.0,
    "3": 1.109,
    "9": 16.63
  },
  "screen_exclude": {
    "0": 18.0,
    "1": 0.0,
    "2": 0.0,
    "3": 0.0,
    "9": 0.0
  }
}

## Design-weighted scope, R2+ and R3 prevalence bounds

{
  "S1_higher_education_lower_bound": {
    "weighted_numerator": 8213.122,
    "known_population_denominator": 10283,
    "estimate": 0.798709,
    "approximate_normal_95pct_ci": [
      0.774885,
      0.822533
    ],
    "standard_error": 0.012155,
    "limitation": "Design-based SRS-WOR estimate, small-sample normal CI, conditional on reviewer reference and stated treatment of uncertain9."
  },
  "S1_or_S9_upper_bound": {
    "weighted_numerator": 8782.672,
    "known_population_denominator": 10283,
    "estimate": 0.854096,
    "approximate_normal_95pct_ci": [
      0.833252,
      0.874941
    ],
    "standard_error": 0.010635,
    "limitation": "Design-based SRS-WOR estimate, small-sample normal CI, conditional on reviewer reference and stated treatment of uncertain9."
  },
  "R2plus_strict_accepted_lower_bound": {
    "weighted_numerator": 546.189,
    "known_population_denominator": 10283,
    "estimate": 0.053116,
    "approximate_normal_95pct_ci": [
      0.039182,
      0.06705
    ],
    "standard_error": 0.007109,
    "limitation": "Design-based SRS-WOR estimate, small-sample normal CI, conditional on reviewer reference and stated treatment of uncertain9."
  },
  "R2plus_or_R9_upper_bound": {
    "weighted_numerator": 1118.839,
    "known_population_denominator": 10283,
    "estimate": 0.108805,
    "approximate_normal_95pct_ci": [
      0.089825,
      0.127785
    ],
    "standard_error": 0.009684,
    "limitation": "Design-based SRS-WOR estimate, small-sample normal CI, conditional on reviewer reference and stated treatment of uncertain9."
  },
  "R3_direct_policy_lower_bound": {
    "weighted_numerator": 424.189,
    "known_population_denominator": 10283,
    "estimate": 0.041251,
    "approximate_normal_95pct_ci": [
      0.028854,
      0.053649
    ],
    "standard_error": 0.006325,
    "limitation": "Design-based SRS-WOR estimate, small-sample normal CI, conditional on reviewer reference and stated treatment of uncertain9."
  },
  "R3_or_R9_upper_bound": {
    "weighted_numerator": 996.839,
    "known_population_denominator": 10283,
    "estimate": 0.09694,
    "approximate_normal_95pct_ci": [
      0.07892,
      0.114961
    ],
    "standard_error": 0.009194,
    "limitation": "Design-based SRS-WOR estimate, small-sample normal CI, conditional on reviewer reference and stated treatment of uncertain9."
  }
}

## Conditional binary screening scope sensitivity

{
  "definition": "Machine positive = include_core/include_policy/include_context; machine negative = screen_exclude ONLY. Human positive = S1. S9 are separately treated as possible nonpositive/positive.",
  "population_scope": "Original final-screening N=10,283, after substantial upstream filtering; NOT original OpenAlex retrieval",
  "uncertainty_scenarios": {
    "S9_assumed_negative": {
      "weighted_TP": 8213.122,
      "weighted_FP": 2051.878,
      "weighted_FN": 0.0,
      "weighted_TN": 18.0,
      "positive_predictive_value": 0.800109,
      "sensitivity_in_FINAL_10283_frame": 1.0,
      "specificity_in_FINAL_10283_frame": 0.008696,
      "negative_predictive_value": 1.0,
      "f1_in_FINAL_10283_frame": 0.888956
    },
    "S9_assumed_positive": {
      "weighted_TP": 8782.672,
      "weighted_FP": 1482.328,
      "weighted_FN": 0.0,
      "weighted_TN": 18.0,
      "positive_predictive_value": 0.855594,
      "sensitivity_in_FINAL_10283_frame": 1.0,
      "specificity_in_FINAL_10283_frame": 0.011997,
      "negative_predictive_value": 1.0,
      "f1_in_FINAL_10283_frame": 0.922178
    }
  },
  "PPV_scope_lower_bound_including_uncertain9_as_negative": {
    "weighted_numerator": 8213.122,
    "known_population_denominator": 10265,
    "estimate": 0.800109,
    "approximate_normal_95pct_ci": [
      0.776244,
      0.823975
    ],
    "standard_error": 0.012176,
    "limitation": "Design-based SRS-WOR estimate, small-sample normal CI, conditional on reviewer reference and stated treatment of uncertain9."
  },
  "PPV_scope_upper_bound_including_uncertain9_as_positive": {
    "weighted_numerator": 8782.672,
    "known_population_denominator": 10265,
    "estimate": 0.855594,
    "approximate_normal_95pct_ci": [
      0.834713,
      0.876475
    ],
    "standard_error": 0.010654,
    "limitation": "Design-based SRS-WOR estimate, small-sample normal CI, conditional on reviewer reference and stated treatment of uncertain9."
  },
  "limitations": [
    "The original classifier has only 18 final-screen exclusions, and the original OpenAlex upstream filters are OUTSIDE the current frame. Near-perfect recall within this frame would be structurally misleading as a claim about initial search sensitivity.",
    "Scope S9 and relevance R9 represent UNRESOLVED text/abstract eligibility; these are extreme-scenario sensitivity bounds, NOT a verified fulltext truth standard.",
    "No model decision class is equated with strict direct-policy R3 or R2plus; include_policy is a pipeline stratum label, not a calibrated human relevance classification.",
    "No empirical claim of model precision can be made for policy-relatedness until a defensible mapping and study target are predeclared. No new human judgments were created."
  ]
}

## Scientific limits

- This analysis is conditional on the PI's assertion that both rating forms are actual independent expert work; workbook metadata says Claude AI, and Phase33 panel rationale is tagged [Adjudicación IA]. Signed/dated expert and panel provenance statements remain essential.
- The reference is based on title and abstract; 74 R9 remain unresolved. Rates include explicitly separate worst-case R9 scenarios, not forced judgments.
- Initial OpenAlex/earlier bibliographic-filter exclusions are outside the 10,283 frame. No inference about the original 199,366 retrieval pipeline's recall/specificity.
- Discipline/topic agreement between original rule labels and expert T/D is not computed here because differently operationalized constructs would require a declared mapping.
- No direct-policy classifier performance is asserted because the machine's include_policy stratum is NOT equivalent to expert R3; see weighted stratified contingency table.
- Design-weighted estimates reflect machine-stratified disproportionate sample; descriptive human agreement was unweighted and must be reported separately.
- The PHASE25 independent 80-case risk-enriched QA showed substantial discrepancies with older consensus and remains an important limitation to describe transparently.
