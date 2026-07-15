# Codex-on-YouTube Task Taxonomy

The taxonomy organizes tasks by the Codex behavior being tested. Existing
catalog IDs remain unchanged.

## A. Playback and tab control

- identify which YouTube tab or player is active;
- pause, play, mute, seek, or change speed on the intended target;
- distinguish playing, paused, buffering, ended, stalled, and live state;
- leave unrelated tabs unchanged;
- restore temporary player changes.

Typical failures: wrong tab, wrong player, ambiguous state, unverified action,
or unrestored state.

## B. Timestamp and temporal evidence

- locate a spoken definition, correction, demonstration, or visual event;
- answer with a timestamp inside an accepted interval;
- use chapters, captions, transcript, or direct playback as permitted;
- distinguish absence of evidence from inability to observe.

Typical failures: wrong timestamp, transcript-only answer for a visual task,
under-observation, or unsupported success claim.

## C. Long-duration observation

- inspect long educational/interview/lecture videos;
- handle long music and ambient videos with limited metadata;
- choose when to watch, seek, or stop;
- avoid excessive observation that does not improve evidence.

Typical failures: over-watching, under-watching, channel misuse, or time-budget
exhaustion.

## D. Live YouTube

- identify live versus recorded state;
- reason about moving live edges and DVR windows;
- inspect live indicators and requested player state;
- stop safely on ads, unavailable streams, or unstable controls.

Typical failures: treating volatile state as fixed, unsafe ad interaction,
incorrect DVR assumptions, or failure to restore temporary settings.

## E. Cross-video and multi-tab tasks

- retain evidence across two or more YouTube videos;
- compare explanations or claims with source-specific timestamps;
- preserve per-tab playback state;
- report insufficient evidence instead of guessing.

Typical failures: source confusion, stale state, wrong-tab actions, and
overconfident synthesis.

## F. Verification and recovery

- verify requested final state using an allowed observation;
- detect and recover from a grounding or action mistake;
- record the mistake rather than presenting the run as clean;
- verify protected-state invariants.

Typical failures: claiming success without evidence, failed recovery, hidden
side effects, and incomplete restoration.

## Track mapping

The deterministic fixture should cover repeatable control, timestamp,
verification, restoration, and cross-tab failures. Live YouTube is required
for ads, consent, UI experiments, real transcript availability, recommendation
state, live streams, and other volatile product behavior. Live public video
extends dated evidence collection across sites and exposes availability,
metadata, cross-site grounding, and timestamp-localization differences without
turning volatile pages into deterministic fixtures.
