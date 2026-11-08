# Phase 28 — Prospective enhanced validation design V0.1 (1,200 main records)

**Scientific status:** planning document, not a completed validation or final statistical pre-registration. This expands the earlier exploratory n=518 planning example. Any final sample size and target metrics must be approved **before** seeing held-out outcome comparisons. Neither manuscript claims nor private human ratings have been altered.

## Why recalibrate rather than simply rating all 10,283 records?

The first 30 cases of Phase28 are a **training/calibration pilot**, not an accuracy sample. The original Phase25 independent QA had severe disagreements with Phase23, and the Phase27 panel was not blind to previous labels. Simply increasing record count with an inconsistent rubric would produce additional disagreement, not a reproducible reference standard. Requiring TWO independent, trained NEW domain experts and an evidence-specific R0/R1/R2/R3/R9 rubric is more important than maximizing sample size.

An entire manual census of 10,283 would require **20,566 independent ratings**, plus arbitration/full-text review. At 5–8 minutes per rating, this would be approximately 1,714–2,742 reviewer-hours across the two reviewers and would not fix an ambiguous codebook. A properly drawn and weighted validation sample is generally preferable when estimating classifier error.

## Phase A — calibration pilot: 30 NEW records

- Same 30 items independently assessed by A and B in separate blinded workbooks, shuffled per rater, with separate copies of versioned pilot codebook V0.2.
- Pilot deliberately balances 10 include_core, 10 include_policy, 10 include_context; it excludes ALL 368 earlier Phase05 cases for clean methodological calibration and does not use the 18 machine-exclude census records already audited.
- Annotate S (scope 0/1/9); R (policy relevance 0/1/2/3/9); T (topic); D (discipline); source evidence and identifiable policy mechanism when R2/3; full-text escalation. No previous human labels, original machine predictions, strata or source IDs are shown.
- Both original forms are frozen and verified before reconciliation. Document confusion matrix, exact agreement, kappa, item-level reasons privately, and revise rubric **before** holdout. A suggested operational calibration floor is 75% agreement for scope and relevance; it is not proof of validity. If the two experts disagree about meaning of R2/R3, pilot more **different** training items, not held-out cases.
- After calibration, release V1.0-VALIDATION and freeze written eligibility criteria, model-output mapping, source coverage, blind assessor roster, decision log, sampling scheme and primary estimands.

## Phase B — enhanced held-out stratified probability validation: provisional n=1,200

Original automated screening population: 10,283 bibliographic records. Phase28 pilot excluded 10 from core, 10 policy, 10 context, yielding a *non-pilot* target population N*=10,253. **This is a different target from 10,283; do not silently generalize beyond it.** The two early bibliographic-filter exclusions (q1_not_article_ready N=11,393; core_not_q1 N=848) are NOT automated screen-exclude records and need a separate assessment if claiming performance of the upstream filtering pipeline.

| AI-screen stratum | Non-pilot frame N_h | Proposed n_h | Fraction |
|---|---:|---:|---:|
| screen_include_core | 9,254 | 800 | 8.65% |
| screen_include_policy | 889 | 290 | 32.62% |
| screen_include_context | 92 | 92 | 100% census |
| screen_exclude | 18 | 18 | 100% census |
| **Total** | **10,253** | **1,200** | **11.70%** |

Draw simple random samples without replacement *within each of the first two strata*. All 92 non-pilot context and 18 exclude records are census for those strata; do not claim zero **human-label** uncertainty just because sampling variance is zero.

**DO NOT exclude the 368 old Phase05 records from the prospective final sampling frame.** Their exclusion would create unequal/zero sampling probabilities in parts of the target frame. If sampled, they must be reevaluated by entirely NEW, genuinely blind assessors without prior labels. Old records can reappear by chance; the 30 pilot records cannot.

At 95% confidence, worst-case binary proportion p_h=0.5, SRS without replacement, fixed N_h above and primary design weights W_h=N_h/10,253, the approximate normal half-width for ONE overall binary proportion is:

1.96 sqrt( sum_h W_h^2 (1 - n_h/N_h) [0.25/(n_h-1)] ) = **0.03019** (about ±3.02 percentage points).

This is a design-based *planning approximation*, NOT a confidence width for rare direct-policy3 recall, classifier sensitivity, conditional PPV or specific machine labels. Within-stratum illustrative worst-case half-widths: core ±3.31 points; policy ±4.73 points; census context/exclude sample variance 0 but reference ambiguity persists.

For positive class R=3, the old samples suggest rarity. A 1,200-item sample might produce too few independent human positives for a precise recall interval. **Before drawing, define a precision/rare-event success criterion or increase the sample / use a predeclared two-phase probability design.** Do NOT add nonprobability challenge items into probability-weighted performance estimates. A separate purposive hard-case set may complement but not replace the probability validation.

## Phase C — dual independent human judgments

- Both new qualified raters must evaluate **all 1,200** records, approximately 2,400 independent title/abstract ratings, with a third arbitrator or consensus panel only AFTER original forms/hashes are archived.
- Nominal capacity if each rating takes 5–8 minutes: 200–320 combined reviewer-hours (100–160 per reviewer), plus conflict resolution and full texts. Schedule this appropriately; do not assume AI can act as the human assessor.
- Per record require scope S, relevance R, topical domain T, discipline D, specific evidence for R2/3, text excerpt/paraphrase, need for full text and reason. Record missing/ambiguous cases rather than resolving by guessing.
- Report exact agreement, nominal/ordinal kappa (with uncertain9 handled explicitly), per-category confusion tables and contextual interpretation of unequal prevalences. Do not let the final panel review retroactively change the original A/B measurement of agreement.

## Phase D — full-text escalation and reference adjudication

- Escalate R9, ambiguous possible eligibility and potentially influential policy-positive cases to full text. If making full-study-eligibility claims, apply duplicate independent full-text eligibility decisions per Cochrane, with documented conflicts and sources; if text is unavailable, label unresolved.
- Arbitration requires case-specific evidence and a traceable written protocol. The same majority vote is not a substitute for content-based resolution, and a panel aware of prior responses is NOT a new independent rater.
- Track availability, reasons for full-text exclusions, duplicates, undecidable cases, taxonomy drift and any change of codebook version.

## Phase E — defensible metrics and estimands

1. Establish scope-positive, policy-at-least-indirect (R2/R3), and strict direct-policy R3 as **separate outcomes**.
2. Define model screening decision mapping to each outcome **before** looking at final reference labels. A class named include_policy does not automatically mean R≥2; original include_core may contain many R2+ records.
3. Report stratified and design-weighted human label prevalence with design variance/CI; only after a valid model-to-human mapping report design-weighted TP/FP/FN/TN and confidence intervals for classifier sensitivity, specificity, PPV, NPV and F1 where identifiable.
4. The machine-exclude class has only 18 items and belongs to a FINAL SCREENING subset already filtered upstream. It cannot support broad claims of negative-class specificity for the full original bibliographic search universe. Retention and retrieval biases must be addressed separately.
5. Report conditional and class-specific precision intervals, missing-text sensitivity, R9 uncertain bounds, primary strict3 versus inclusive2+, and robustness to stratum weighting. Do not report unconditional original-universe classifier performance unless an appropriate upstream exclusion/retrieval sampling design is included.
6. Keep ALL Phase21–27 negative QC results visible as historical method-development evidence, not overwrite them or claim that the new codebook governed earlier ratings.

## Conditional optional stage — upstream bibliographic filters

If the manuscript evaluates the ENTIRE bibliographic-selection workflow, specify distinct probability audits of the q1_not_article_ready (11,393) and core_not_q1 (848) populations. A preliminary **planning-only** 200 and 100 additional records could inform filter leakage, but needs outcome/sample size justification and separate appropriate human eligibility rules. These are NOT final AI-screen classifier negatives and must not contaminate the 1,200-case four-stratum estimator.

## Scientific stop rules and status

- Pilot/codebook V1.0 and model estimands must be frozen before final sample generation.
- Two new genuine independent reviewers must not receive historical A/B/consensus/Phase24/Phase27 or AI labels.
- The 1,200 sample size is a recommended **starting design, not a guaranteed reviewer-proof metric**. Power/CI width for rare R3 must be verified and potentially increased before sampling.
- No new pilot, 1,200-case holdout or human rating data are generated by this document.

**References:** PRISMA 2020 item8 https://pmc.ncbi.nlm.nih.gov/articles/8005925/ ; Cochrane Handbook ch4 §4.6.4 https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-04 ; NIH Library screening pilot https://www.nihlibrary.nih.gov/services/evidence-synthesis/select-collect-synthesize/screening .
