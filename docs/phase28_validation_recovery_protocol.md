# Phase 28 — Protocol to recover scientific validity of AI policy screening

**Status: methodological recovery protocol (proposal only).** No new human ratings or classifier-performance estimates have been generated.

## Why the Phase27 reconciliation is not sufficient

- Phase05 sampled **368 records** across six distinct strata: screen_include_core N=9264/n=120; screen_include_policy N=899/n=80; screen_include_context N=102/n=40; screen_exclude N=18/n=18; q1_not_article_ready N=11393/n=80; core_not_q1 N=848/n=30.
- The **first four** are the final AI-screening frame (N=10283). The other two are **earlier bibliographic-filter exclusions** and must NOT be treated as AI classifier negatives.
- Phase21 human A/B independent ratings disagreed on relevance=89, discipline=218, primary policy dimension=183 of 368; unique records with any disagreement=316.
- Phase23 adjudicated 316 and retained 52 unanimously coded items. Descriptive design-weighted fractions (conditional on the adjudication and Phase05 sample design): relevance code0 11.6375%; code1 50.7917%; codes2+3 35.7763% (direct policy code3 3.7538% as a SUBSET of code2+); uncertain9 1.7945%. These are NOT independently validated classifier-performance statistics.
- Phase25 **risk-enriched** (NOT representative) 80-case blind QA observed relevance exact agreement 33/80 and unweighted kappa 0.31447 on 67 jointly non-uncertain items; discipline agreement 22/80, kappa 0.13755; post-hoc normalized policy agreement 9/80, kappa 0.00647. Policy QA did NOT originally use the approved coding taxonomy.
- Phase27 panel saw prior ratings (NOT blinded): retained Phase23 relevance on 78/80, discipline 80/80, primary policy 79/80, but matched original independent QA on relevance 34/80, discipline 22/80, posthoc normalized policy 9/80. Thirteen selected QA cases remain uncertain on relevance. High retention of a *visible earlier consensus* does not independently establish its accuracy.

Do not retrospectively overwrite original A/B, adjudicator, QA or panel records, delete unfavorable observations, or present Phase27 as independent adjudication.

## Two scientifically defensible routes

### Route A — descriptive/exploratory manuscript now

Report Phase21 original agreement, Phase23 original human adjudication, and conditional stratified frequencies distinctly. Disclose Phase25's genuine independent QA disagreement and intentional risk enrichment, along with Phase27's non-blinded panel disposition. Restrict claims to the evidence. Do not assert corpus-wide accuracy, precision, recall or sensitivity. Mark the originally estimated Phase23 prevalences *provisional and conditional*, not validated truth. Separate preceding bibliographic exclusions from final AI-screening classes. Report uncertainty and the 13 unresolved reviewed cases.

### Route B — independent prospective validation before classifier-performance claims

**1. Recalibrate a reproducible codebook BEFORE new validation decisions.** Clarify: scope 0=outside AI in higher education; 1=AI in HE without explicit policy inquiry; 2=AI/HE study with demonstrable INDIRECT institutional-policy or governance implications; 3=study investigates policies, regulation, institutional rules or governance as an explicit PRIMARY object; 9=title/abstract evidence insufficient, requires escalation. Document positive and negative examples for boundaries 0/1, 1/2, 2/3 and 9. A generic educational recommendation or a passing reference to ChatGPT cannot alone justify a direct policy score.

**Separate scope, policy relevance and topical domain.** Teaching-learning, assessment and ethics-integrity are thematic topics; these labels alone do not establish that a study actually investigates institutional policy. Distinguish the main topic from the actual policy instrument/mechanism, if one is evidenced. Specify hierarchical and interdisciplinary coding rules, decision logs and handling of review articles. Preserve codebook version history; do NOT claim a revised codebook governed Phase21.

**2. Calibrate on 20–30 pilot records, not included in subsequent validation.** At least two trained, independent assessors, blinded to the original model labels, sampling stratum and previous human ratings, code every pilot independently, then reconcile interpretations. Freeze instructions, rubric, data schema, reviewers, classifier decision mapping and primary estimands before selecting the held-out evaluation cases.

**3. Draw a NEW stratified probability sample from the FOUR final AI-screening strata.** A planning-only example: n=180 from screen_include_core, n=100 from screen_include_policy, n=62 from screen_include_context, census n=18 from screen_exclude (360 total). This is NOT a power-justified final sample size: pre-compute required width/precision and rare-class power before sampling. Prefer previously unseen items where available and reviewers with no exposure to earlier case decisions. Because all 18 screen_exclude records were already sampled in Phase05, independent *new* assessors must be blinded to those past scores if re-used. Keep all real identifiers, strata, source metadata and AI labels in a protected key, never in reviewer workbooks.

**4. Two truly independent title/abstract assessments and predeclared conflict protocol.** Collect structured reasons including brief text evidence and required full text. Freeze the two completed books before any discussion. Compute confusion matrices and observed agreement, category-specific precision of estimates, ordinal and nominal inter-rater kappa appropriately. A numeric kappa threshold alone does not validate the construct.

**5. Full-text escalation** for uncertainty 9 and genuinely possibly eligible studies. When final study inclusion is claimed, use two independent full-text decisions with pre-specified conflict arbitration and transparent unresolved cases. Do not silently force uncertain into positive or negative categories.

**6. Clearly pre-specify distinct estimands.** Scope positive (>=1), policy at least indirect (>=2), directly about AI policy (=3) are different human outcomes. They are not automatically equivalent to the machine's include_core, include_policy or include_context classes; justify any mapping *before* model-versus-reference analysis. Use stratum-specific confusion matrices, stratified sample-design weights and uncertainty estimates. Early q1_not_article_ready and core_not_q1 must remain analytically separate. Sensitivity analyses: uncertain cases; inclusive2+ versus strict3; full text versus title/abstract; and deviations associated with previous B-dominant decisions.

## Minimum go/no-go conditions

- GO to validation-performance claims only with a versioned prospective codebook, genuine assessor independence, frozen source and machine decisions, justified sample design, documented treatment of uncertainty, and explicit disclosure of unfavorable QA results.
- HOLD validation claims if relying only on Phase23 adjudication + non-blinded Phase27 panel. Route A remains a publishable-style *descriptive study design* if all limitations and estimands are correctly described; publication suitability still depends on the complete paper and journal.
- No AI decisions or human consensus are created or modified by this protocol.

## Reporting and methods references

- PRISMA 2020, item 8: explicit independence and number of screeners at record/full-text levels, disagreement resolution and role of automated screening.
  https://pmc.ncbi.nlm.nih.gov/articles/8005925/
- Cochrane Handbook for Systematic Reviews of Interventions, v6.5.1 (2025), Chapter 4, §4.6.4: independent eligibility judgements and pre-defined disagreements, with full-text confirmation where possible.
  https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-04
- NIH Library evidence synthesis screening and pilot guidance:
  https://www.nihlibrary.nih.gov/services/evidence-synthesis/select-collect-synthesize/screening
