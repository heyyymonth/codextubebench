# Archived: Risks and Mitigations

| Risk | Consequence | Mitigation |
| --- | --- | --- |
| Live YouTube drift, ads, consent, or experiments | Non-reproducible failures | Controlled fixture is primary; live tasks are optional, read-only, pinned, and drift-checked |
| Copyright or redistribution limits | Dataset cannot be released | Benchmark-authored or clearly licensed media with checksums and provenance |
| Transcript leakage makes tasks trivial | Benchmark measures search rather than media understanding | Separate access modes; visual-only evidence tasks; channel-specific obligations |
| Overfitting to fixed timestamps | Memorization replaces observation | Held-out fixture variants, shifted timelines, paraphrases, and secret test tasks |
| Hidden DOM gives unfair advantage | Incomparable results | Strict capability policies and separate leaderboards |
| Agent disturbs accounts or unrelated media | Safety and validity failure | Isolated profiles, action allowlists, trajectory auditing, local fixture writes only |
| Transient side effects disappear by final state | Unsafe trajectory scores as clean | Event-level mutation audit; restoration does not erase incidents |
| Background playback counted as watching | Inflated evidence coverage | Separate player exposure from attended observation |
| Metric gaming through 2x playback or scrubbing | Misleading efficiency | Report content-time, playback wall-time, point samples, and seek jumps separately |
| Human reference is treated as uniquely optimal | Biased efficiency | Multiple mode-matched references and documented alternative valid strategies |
| Judge-model bias in L4 rubrics | Unstable workflow results | Exact gates first, blinded calibrated rubrics, human agreement, versioned judge settings |
| Provider/model drift | Results cannot be repeated | Dated model IDs, prompt/config digests, raw lab metadata, repeated runs |
| Raw traces leak private or authenticated state | Privacy/security incident | No personal profiles; restricted storage; aggregate-only paper export |
| Benchmark tasks contain prompt injection | Scope expansion or secret access | Page content is untrusted; manifest authority; fake canaries; fail-closed actions |
| Fixture or oracle bugs are counted as agent failures | Invalid conclusions | Eligibility evaluator, negative controls, reset tests, replayable traces |
| Composite score hides failure modes | Misleading rankings | Publish metric vector and safe grounded success; composite remains secondary |
| Novelty claim is too broad | Paper rejection or inaccurate scholarship | Explicitly position against VideoWebArena and LivingScreen; refresh literature before submission |

## Platform compatibility

- Public live tasks prohibit likes, comments, subscriptions, saves, reports,
  purchases, chat, account changes, and public posting.
- Write tasks use only benchmark-owned local fixtures or separately approved
  sandbox resources and have cleanup scripts.
- Rate limits and normal user-visible interaction paths are respected.
- Private, paywalled, or personal YouTube content is excluded unless a separate
  authorized protocol is approved.

## Human-subject considerations

Human baseline collection must document consent, compensation, data retention,
PII exclusion, and the institution's ethics/IRB determination. Avoid collecting
personal browsing histories or account state.
