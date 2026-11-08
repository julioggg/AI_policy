# Phase36 — geographic availability bias and 5000 selection trace

{
  "status": "country_incidence_bias_fulltext_and_DOI_proxy_attempts_NOT_exact_5000_selection_proof",
  "original_counts": {
    "screening_final_n": 10283,
    "screening_included_n": 10265,
    "fulltext_downloaded_or_preexisting_n": 3656,
    "attempts_n": 5000,
    "original_source_bad_country_strings_in_parent": 1685,
    "original_source_bad_country_strings_in_fulltext": 587
  },
  "attempt_DOI_linkage_diagnostics": {
    "manifest_records": 5000,
    "distinct_nonblank_attempt_dois": 4835,
    "missing_doi": 164,
    "unmatched_doi": 0,
    "ambiguous_multiple_included_OpenAlex_ids": 2,
    "repeated_dois_in_attempt_manifest": 1,
    "unambiguously_linked_unique_included_records": 4834,
    "linked_DOI_records_are_NOT_exact_original_5000_membership": true,
    "manifest_status_counts": {
      "downloaded": 3655,
      "error_ConnectTimeout": 62,
      "error_ConnectionError": 30,
      "error_ReadTimeout": 13,
      "error_SSLError": 42,
      "error_TooManyRedirects": 1,
      "exists": 1,
      "http_400": 2,
      "http_403": 922,
      "http_404": 73,
      "http_405": 2,
      "http_410": 1,
      "http_429": 15,
      "http_500": 3,
      "http_503": 13,
      "not_pdf_text/html": 1,
      "not_pdf_text/html; charset=utf-8": 29,
      "not_pdf_text/html;charset=utf-8": 1,
      "too_small": 134
    }
  },
  "fulltext_largest_differences": [
    {
      "country": "ID",
      "parent_records_with_country": 378,
      "subset_records_with_country": 171,
      "parent_percent": 3.682,
      "subset_percent": 4.677,
      "difference_percentage_points": 0.995
    },
    {
      "country": "US",
      "parent_records_with_country": 992,
      "subset_records_with_country": 323,
      "parent_percent": 9.664,
      "subset_percent": 8.835,
      "difference_percentage_points": -0.829
    },
    {
      "country": "ZA",
      "parent_records_with_country": 120,
      "subset_records_with_country": 72,
      "parent_percent": 1.169,
      "subset_percent": 1.969,
      "difference_percentage_points": 0.8
    },
    {
      "country": "MY",
      "parent_records_with_country": 115,
      "subset_records_with_country": 64,
      "parent_percent": 1.12,
      "subset_percent": 1.751,
      "difference_percentage_points": 0.63
    },
    {
      "country": "RU",
      "parent_records_with_country": 64,
      "subset_records_with_country": 42,
      "parent_percent": 0.623,
      "subset_percent": 1.149,
      "difference_percentage_points": 0.525
    },
    {
      "country": "PH",
      "parent_records_with_country": 136,
      "subset_records_with_country": 65,
      "parent_percent": 1.325,
      "subset_percent": 1.778,
      "difference_percentage_points": 0.453
    },
    {
      "country": "GB",
      "parent_records_with_country": 341,
      "subset_records_with_country": 110,
      "parent_percent": 3.322,
      "subset_percent": 3.009,
      "difference_percentage_points": -0.313
    },
    {
      "country": "IT",
      "parent_records_with_country": 54,
      "subset_records_with_country": 8,
      "parent_percent": 0.526,
      "subset_percent": 0.219,
      "difference_percentage_points": -0.307
    },
    {
      "country": "CA",
      "parent_records_with_country": 141,
      "subset_records_with_country": 60,
      "parent_percent": 1.374,
      "subset_percent": 1.641,
      "difference_percentage_points": 0.268
    },
    {
      "country": "VN",
      "parent_records_with_country": 90,
      "subset_records_with_country": 40,
      "parent_percent": 0.877,
      "subset_percent": 1.094,
      "difference_percentage_points": 0.217
    },
    {
      "country": "NG",
      "parent_records_with_country": 51,
      "subset_records_with_country": 26,
      "parent_percent": 0.497,
      "subset_percent": 0.711,
      "difference_percentage_points": 0.214
    },
    {
      "country": "MX",
      "parent_records_with_country": 54,
      "subset_records_with_country": 27,
      "parent_percent": 0.526,
      "subset_percent": 0.739,
      "difference_percentage_points": 0.212
    }
  ],
  "attempt_proxy_largest_differences": [
    {
      "country": "ZA",
      "parent_records_with_country": 120,
      "subset_records_with_country": 84,
      "parent_percent": 1.169,
      "subset_percent": 1.738,
      "difference_percentage_points": 0.569
    },
    {
      "country": "ID",
      "parent_records_with_country": 378,
      "subset_records_with_country": 204,
      "parent_percent": 3.682,
      "subset_percent": 4.22,
      "difference_percentage_points": 0.538
    },
    {
      "country": "GB",
      "parent_records_with_country": 341,
      "subset_records_with_country": 181,
      "parent_percent": 3.322,
      "subset_percent": 3.744,
      "difference_percentage_points": 0.422
    },
    {
      "country": "CN",
      "parent_records_with_country": 490,
      "subset_records_with_country": 249,
      "parent_percent": 4.774,
      "subset_percent": 5.151,
      "difference_percentage_points": 0.378
    },
    {
      "country": "ES",
      "parent_records_with_country": 131,
      "subset_records_with_country": 77,
      "parent_percent": 1.276,
      "subset_percent": 1.593,
      "difference_percentage_points": 0.317
    },
    {
      "country": "AU",
      "parent_records_with_country": 248,
      "subset_records_with_country": 131,
      "parent_percent": 2.416,
      "subset_percent": 2.71,
      "difference_percentage_points": 0.294
    },
    {
      "country": "MY",
      "parent_records_with_country": 115,
      "subset_records_with_country": 68,
      "parent_percent": 1.12,
      "subset_percent": 1.407,
      "difference_percentage_points": 0.286
    },
    {
      "country": "RU",
      "parent_records_with_country": 64,
      "subset_records_with_country": 43,
      "parent_percent": 0.623,
      "subset_percent": 0.89,
      "difference_percentage_points": 0.266
    },
    {
      "country": "MX",
      "parent_records_with_country": 54,
      "subset_records_with_country": 38,
      "parent_percent": 0.526,
      "subset_percent": 0.786,
      "difference_percentage_points": 0.26
    },
    {
      "country": "PH",
      "parent_records_with_country": 136,
      "subset_records_with_country": 76,
      "parent_percent": 1.325,
      "subset_percent": 1.572,
      "difference_percentage_points": 0.247
    },
    {
      "country": "EC",
      "parent_records_with_country": 31,
      "subset_records_with_country": 26,
      "parent_percent": 0.302,
      "subset_percent": 0.538,
      "difference_percentage_points": 0.236
    },
    {
      "country": "PE",
      "parent_records_with_country": 38,
      "subset_records_with_country": 28,
      "parent_percent": 0.37,
      "subset_percent": 0.579,
      "difference_percentage_points": 0.209
    }
  ],
  "selection_script_AST": {
    "available": true,
    "filename": "10_download_open_access_pdfs.py",
    "statements_lexically_detected": [
      {
        "line": 82,
        "method": "sort_values",
        "literal_args": [
          {
            "key": "ascending",
            "value": [
              false,
              false
            ]
          }
        ]
      },
      {
        "line": 161,
        "method": "to_csv",
        "literal_args": []
      },
      {
        "line": 164,
        "method": "to_csv",
        "literal_args": []
      },
      {
        "line": 167,
        "method": "to_csv",
        "literal_args": []
      },
      {
        "line": 85,
        "method": "head",
        "literal_args": []
      },
      {
        "line": 167,
        "method": "head",
        "literal_args": [
          {
            "key": "head_arg",
            "value": 3000
          }
        ]
      }
    ],
    "status": "STATIC AST HINTS ONLY: not verified to be executed; original code must be manually checked.",
    "original_script_sha256_kept_private": false
  },
  "limitations": [
    "Parent-to-attempt comparison is DOI-linked PROXY, not exact 5000 selection, because manifest lacks OpenAlex IDs.",
    "Country counts are multi-affiliation incidence, not exclusive national shares or fractionalized author credit; non-geocoded entries remain explicitly missing.",
    "No new source documents were retrieved. Download availability and initial selection are distinct bias mechanisms.",
    "AST detection identifies possible ranking and head/selection statements; does not prove these statements were executed or all inputs preserved.",
    "This script does not assert a true stratified geographic probability estimator or causal explanation of selection bias.",
    "Do not claim this report proves full-text eligibility or policy relevance, and do not extrapolate it to pre-filter OpenAlex search hits."
  ]
}
