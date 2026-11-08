# Phase 19 — Scientific synthesis and reporting safeguards

Source of truth: [Phase 14](../reports/phase14/summary.md), [Phase 16](../reports/phase16/summary.md), [Phase 18](../reports/phase18/summary.md) and [Phase 19](../reports/phase19/summary.md). This document reports only aggregates; no publication names, private group codes, evaluator comments or article identifiers are published here.

## A. Matched computational corpus

The candidate embeddings used the same 3,629 body-usable publications from 3,644 explicit full-text acceptances. Mean-pooling of body-text chunks rather than legacy one-pass full-text encodings was motivated by independent evidence of severe transformer input truncation. The source PDFs, however, were already subject to character limits, and body segmentation was heuristic. It would therefore be incorrect to claim exhaustive processing of full documents.

The 18-topic body-chunk model achieved a cosine silhouette of **0.100827**, median across-seed ARI **0.54807**, median 80%-subsample ARI **0.49320**, with smallest cluster **44**. The equal-weight hybrid 18-topic model achieved silhouette **0.076961**, median across-seed ARI **0.63437**, median subsample ARI **0.60312**, smallest cluster **63**. Consequently, **body k18** presents better geometric separation, whereas **hybrid k18** presents higher tested clustering stability. These are *internal algorithmic* diagnostics, not evidence of policy validity.

## B. Human assessment before adjudication

Two researchers independently scored 48 anonymized topic clusters—12 from body k12, 18 from body k18 and 18 from hybrid k18—using seven title/abstract/body-excerpt examples per cluster (three central, three random and one peripheral). Each reviewed 336 document–cluster cases. For document-to-topic membership, raw agreement was **91.667%** and Cohen κ **0.73370** (28 disagreements). For document policy relevance, raw agreement was **47.619%**, quadratic-weighted Cohen κ **0.44784** (176 disagreements). The 48 clusters included **31 disagreements** about cluster-level policy relevance. These agreement coefficients characterize human-rater consistency and must not be interpreted as topic-model accuracy.

## C. Adjudication and final descriptive comparison

All **48 groups** received five manually completed consensus fields (240 cells) and all **189 unique disputed documents** received three consensus fields (567 cells); the 189 include 28 disagreements about membership, 176 about policy relevance, and 15 overlapping cases. The 147 documents without A/B disagreement retained their original matching scores; no new independent review was inferred for these.

| Expert-consensus metric | Body k12 | Body k18 | Equal hybrid k18 |
| --- | ---: | ---: | ---: |
| Topic groups assessed | 12 | 18 | 18 |
| Documents assessed | 84 | 126 | 126 |
| Mean coherence (1–5) | 2.91667 | **3.50000** | **3.50000** |
| Mean distinctiveness (1–5) | 2.00000 | 2.33333 | **2.44444** |
| Mean topic-level policy relevance (0–3) | 1.66667 | **1.77778** | 1.66667 |
| Fraction of documents belonging to assigned topic | 0.75000 | **0.81746** | 0.79365 |
| Mean document-level policy relevance (0–3) | 1.34524 | **1.55556** | 1.39683 |
| Documents with policy score ≥2 | 0.41667 | **0.54762** | 0.47619 |
| Documents with direct policy score 3 | 0.04762 | **0.09524** | 0.03175 |

**Interpretation:** body k18 is the most defensible *provisional primary scientific representation* among these preselected candidates because it ties for highest adjudicated coherence and has the strongest sample-level policy relevance and group membership. Equal-weight hybrid k18 is a necessary sensitivity/robustness comparator: it produced slightly higher topic distinctiveness and more stable k18 KMeans partitions across tested seeds and subsamples. The evidence does **not** justify saying that body k18 is statistically or universally superior.

## D. Limitations that must accompany any manuscript claim

1. The seven document examples per cluster were selected for interpretability, not as a simple random, independently sampled sample from each model's full membership. Central cases were deliberately overrepresented; percentages cannot be generalized to the 3,629-document corpus.
2. There are only 12 or 18 evaluated groups per model. Documents can recur across candidate models, and human ratings depend on which cluster context is shown. A naive pooled test of independence or significance would be invalid. No inferential model-comparison p value or confidence interval has been computed.
3. The original 2-rater agreement coefficients are maintained. The adjudicator observed the independent ratings and therefore is not a third blind independent evaluator; reconciliation cannot erase initial disagreements.
4. Model-specific topic labels, descriptions, representative texts and an interpretable final taxonomy remain in protected CEDIA files. The aggregated reports alone cannot establish semantic topic names or substantiate their narrative interpretation; an expert must inspect them before inserting a named 18-topic structure into the manuscript.
5. Full-text availability is selected and strongly biased relative to the bibliographic population. The sentence encoder is truncated per input, body extraction is heuristic, and stored PDF text may be length-capped.
6. The separate 368-record Phase05 stratified eligibility/screening human validation is outstanding. Its early-filter exclusions must not be misrepresented as AI-classifier false negatives; screening performance will require stratum-specific design-based reporting.
7. All original manuscript statements about topic prevalence, growth, policy impact or disciplinary composition require re-running appropriate calculations using the final selected assignment and checking provenance, denominator, and sampling restrictions. No such claims can be inferred from the tables above alone.

## E. Conservative draft paragraph for manuscript adaptation (English)

> To assess the interpretability of alternative text representations, we compared three pre-specified cluster configurations on the matched body-usable subset and conducted a blinded, two-rater semantic review of 48 candidate topics. Seven documents were selected per topic to represent central, randomly sampled and peripheral cases. Independent reviewers assessed thematic coherence, distinctiveness, document membership and policy relevance; disagreements were subsequently adjudicated without displaying the underlying model identity. The body-text representation with 18 clusters and the equal-weight hybrid representation with 18 clusters each obtained a mean adjudicated coherence rating of 3.50/5. The body-text model had a higher mean adjudicated topic-level policy relevance (1.78/3 versus 1.67/3), a higher proportion of assessed documents judged to belong to their assigned topic (81.7% versus 79.4%), and a higher proportion with at least indirect policy relevance (54.8% versus 47.6%). Conversely, the hybrid produced slightly more distinctive topics (2.44/5 versus 2.33/5) and greater stability across tested KMeans initializations. We therefore regard the body-based 18-topic solution as a provisional interpretive representation, while retaining the hybrid as a computational sensitivity analysis. These results are descriptive of an intentionally enriched seven-document-per-topic validation sample, not evidence of corpus-level classification accuracy or statistical superiority.

**Do not publish as a completed manuscript revision without checking the final 18-topic names and all paper-specific context.**
