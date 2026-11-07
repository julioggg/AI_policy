# Phase 5 — Blinded human validation protocol

## Scope
The manuscript's computational screening and discipline/policy classification require independent human validation. Automated model predictions are not a gold standard. Two researchers should evaluate the same stratified records independently, blinded to machine labels and to each other's ratings, then adjudicate disagreements.

Three different constructs must remain distinguishable:
1. AI research in higher education: any study of AI in postsecondary settings.
2. Policy-relevant AI in higher education: studies with explicit, defensible institutional implications for governance, assessment rules, academic integrity, privacy, equity, literacy or implementation.
3. Direct AI-policy research: studies in which policy, governance, regulations, institutional rules, safeguards or policy effectiveness are main objects of research.

## Coding schema
For each title/abstract, use source text only, escalating uncertain cases to full text where legally available.

**relevance_code**
- 0: Outside AI in higher education.
- 1: AI in higher education without demonstrable policy relevance.
- 2: Policy-relevant AI in higher education but policy is not the primary object.
- 3: Direct study of AI governance/policy in higher education.
- 9: Uncertain / insufficient information.

**discipline_code**, one of ssh, engineering, health_sciences, general_he, uncertain.

**primary_policy_code**, one of teaching_learning, assessment, ethics_integrity, governance_policy, research_scholarship, ai_literacy_training, equity_access, privacy_security, general_policy, not_applicable, uncertain.

**reason**: short explanation grounded in the publication, including ambiguity notes and any secondary dimensions. Do not assign policy relevance just because a publication mentions ChatGPT.

## Planned sample: nominally 368 records
- 120 final screening include_core.
- 80 final screening include_policy.
- 40 final screening include_context.
- All 18 final screening exclude records.
- 80 excluded between q1_refined and article_ready.
- 30 excluded between core and q1_refined.

Two earlier-stage excluded groups are deliberately separate from final AI screening; their classification errors must NOT be reported as final AI-screening recall errors.

This stratified design oversamples small classes. Do not report unweighted pooled precision/recall as if it represented the parent population. Report per-stratum confusion matrices, inter-rater agreement and, where justified, inclusion-probability-weighted estimates with confidence intervals.

## Privacy
The rater sheets and private sampling key include titles, abstracts and OpenAlex IDs and must remain exclusively outside the public repository, under the CEDIA directory ~/ai_policy_validation_private. Publish only stratum counts and aggregate metrics after human evaluation. Never upload raw rater sheets, abstracts, keys, PDF or raw text to public GitHub.

## Workflow
1. Generate sheets and private key, with reproducible random seed.
2. Raters A and B annotate independently and remain blind to strata and machine labels.
3. Reconcile disagreements only after preserving independent decisions.
4. Independently quantify agreement and classifier metrics; label adjudicated categories correctly.
5. Provide documented limitations; human review of titles/abstracts is not full-text risk-of-bias assessment.

No human review can be claimed before raters actually complete the coding.
