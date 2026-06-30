# Brief Background

TubeBench is not organized around a novelty claim. Its practical question
is whether Codex can complete YouTube browser tasks safely and correctly.

WebArena and OSWorld establish end-to-end web/computer-use evaluation.
VisualWebArena emphasizes visual grounding. LivingScreen treats observation as
a cost-bearing action on short-video interfaces. VideoWebArena and
Video-BrowseComp study video-based retrieval and temporal evidence.

Those projects provide useful methods, but they do not directly answer the
operational question used here:

> What does Codex actually do on long-form YouTube tasks, which actions and
> observations lead to success, and where does it fail?

TubeBench therefore focuses on trace capture, YouTube player/tab state,
verification, side effects, restoration, timestamp evidence, and reproducible
failure replay. Any comparative or first-of-kind claim requires a separate
documented literature review and empirical evidence.

Primary references:

- [WebArena](https://arxiv.org/abs/2307.13854)
- [VisualWebArena](https://arxiv.org/abs/2401.13649)
- [OSWorld](https://arxiv.org/abs/2404.07972)
- [VideoWebArena](https://arxiv.org/abs/2410.19100)
- [LivingScreen](https://arxiv.org/abs/2606.04701)
