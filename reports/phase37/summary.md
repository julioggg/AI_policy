# Phase37 — corrected country string parser, preservation of Phase36

{
  "status": "phase37_corrected_semicolon_ISO2_country_incidence_with_remaining_source_cautions",
  "included_country_parser_diagnostics": {
    "previously_recognized": 5817,
    "semicolon_iso2_recovered": 1685,
    "empty": 2763
  },
  "fulltext_country_parser_diagnostics": {
    "semicolon_iso2_recovered": 587,
    "previously_recognized": 2214,
    "empty": 855
  },
  "original_five_thousand_DOI_proxy_summary": {
    "attempts_n": 5000,
    "unambiguous_matched_unique_publications": 4834,
    "attempts_without_doi": 164,
    "ambiguous_DOI_attempts": 2,
    "unmatched_DOI_attempts": 0,
    "manifest_no_openalex_id": true,
    "precise_5000_original_member_selection_reproduced": false
  },
  "selection_tracing": {
    "script_available": true,
    "MAX_PDFS_literal_assignments": [
      5000
    ],
    "sort_operations": [
      {
        "line": 82,
        "keys_match_priority_then_citations": true,
        "both_descending": true
      }
    ],
    "head_operations": [
      {
        "line": 85,
        "uses_MAX_PDFS": true,
        "literal_limit": null
      }
    ],
    "priority_score_assignment_nodes": 1,
    "selection_pipeline_explicit_priority_score_cited_by_count_descending": true,
    "selection_pipeline_has_head_MAX_PDFS": true,
    "caution": "STATIC source inspection only. Definition of priority_score, original data ordering, and executed-version identity require separate verification."
  },
  "largest_corrected_shifts": [
    {
      "country": "US",
      "parent_records_with_country": 1524,
      "subset_records_with_country": 498,
      "parent_percent": 14.847,
      "subset_percent": 13.621,
      "difference_percentage_points": -1.225
    },
    {
      "country": "ID",
      "parent_records_with_country": 492,
      "subset_records_with_country": 216,
      "parent_percent": 4.793,
      "subset_percent": 5.908,
      "difference_percentage_points": 1.115
    },
    {
      "country": "GB",
      "parent_records_with_country": 654,
      "subset_records_with_country": 202,
      "parent_percent": 6.371,
      "subset_percent": 5.525,
      "difference_percentage_points": -0.846
    },
    {
      "country": "ZA",
      "parent_records_with_country": 167,
      "subset_records_with_country": 90,
      "parent_percent": 1.627,
      "subset_percent": 2.462,
      "difference_percentage_points": 0.835
    },
    {
      "country": "PH",
      "parent_records_with_country": 181,
      "subset_records_with_country": 85,
      "parent_percent": 1.763,
      "subset_percent": 2.325,
      "difference_percentage_points": 0.562
    },
    {
      "country": "RU",
      "parent_records_with_country": 97,
      "subset_records_with_country": 55,
      "parent_percent": 0.945,
      "subset_percent": 1.504,
      "difference_percentage_points": 0.559
    },
    {
      "country": "IT",
      "parent_records_with_country": 118,
      "subset_records_with_country": 22,
      "parent_percent": 1.15,
      "subset_percent": 0.602,
      "difference_percentage_points": -0.548
    },
    {
      "country": "MY",
      "parent_records_with_country": 240,
      "subset_records_with_country": 105,
      "parent_percent": 2.338,
      "subset_percent": 2.872,
      "difference_percentage_points": 0.534
    },
    {
      "country": "VN",
      "parent_records_with_country": 124,
      "subset_records_with_country": 61,
      "parent_percent": 1.208,
      "subset_percent": 1.668,
      "difference_percentage_points": 0.461
    },
    {
      "country": "EC",
      "parent_records_with_country": 60,
      "subset_records_with_country": 34,
      "parent_percent": 0.585,
      "subset_percent": 0.93,
      "difference_percentage_points": 0.345
    },
    {
      "country": "PE",
      "parent_records_with_country": 54,
      "subset_records_with_country": 31,
      "parent_percent": 0.526,
      "subset_percent": 0.848,
      "difference_percentage_points": 0.322
    },
    {
      "country": "AU",
      "parent_records_with_country": 426,
      "subset_records_with_country": 163,
      "parent_percent": 4.15,
      "subset_percent": 4.458,
      "difference_percentage_points": 0.308
    }
  ],
  "limitations": [
    "Country entries represent one or more institutional-country affiliations for each work, not a fractionalised country-attribution model.",
    "Only strict two-letter semicolon tokens were recovered; if semicolon_unrecognized remains nonzero, report the unparsed source counts before using geographic conclusions.",
    "No attempt was made to impute empty countries, which are distinct from unparsed country strings.",
    "The fulltext subset was nonrandomly prioritised and subject to retrieval failures; descriptive shifts are not automatically statistically significant.",
    "The 5000 attempted records have no OpenAlex IDs in manifest; matches by unambiguous DOI remain proxy evidence.",
    "Static AST confirms source statements but not the exact historical version executed or source of priority_score.",
    "The aggregate does not validate scientific paper eligibility, classifier relevance or inferences about country-specific research quality."
  ]
}
