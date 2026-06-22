# Archived: LongFormMediaBench Research Thesis

## Thesis

Long-form YouTube is an interactive information environment, not merely a video
input. An agent must decide what to watch, where to seek, whether to use the
player, transcript, chapters, or captions, when it has enough evidence, how to
preserve playback and tab state, and how to verify an answer. Existing web,
computer-use, and video-understanding benchmarks measure important parts of
this problem, but the reviewed set does not center this exact combination.

LongFormMediaBench tests that missing combination. Its controlled core uses
benchmark-owned YouTube-like fixtures with deterministic transcripts, captions,
chapters, player state, reset logic, and hidden evaluator oracles. A separate
live track uses public YouTube pages for read-only external-validity evaluation.
The deterministic core is the reproducible scoring track; the live track
measures dated product behavior and platform drift.

## Research object

The benchmark treats information acquisition as an agent action with measurable
cost. A successful agent may still be poor if it watches forty minutes to find
a thirty-second answer, answers without observing required evidence, uses a
transcript for a visual-only claim, disturbs unrelated media, or fails to verify
the final state. The benchmark therefore evaluates a trajectory, not only a
final answer.

Each run records:

- observations, browser actions, tool calls, and verification events;
- unique watched intervals and repeated exposure;
- transcript, caption, chapter, description, comment, search, DOM,
  accessibility, JavaScript, and player-state access;
- pre-state, transient mutations, post-state, and protected invariants;
- final answers or artifacts with source and timestamp provenance;
- steps, latency, model calls, tokens, cost, and benchmark Git revision.

## Four access classes

The same semantic task may be evaluated under different access policies:

1. `gui_native`: rendered screenshots, recordings, audio, pointer, and keyboard.
2. `ui_assisted`: GUI-native plus information visible to a normal user through
   transcripts, captions, chapters, descriptions, comments, and platform
   search.
3. `instrumented_browser`: UI-assisted plus logged DOM, accessibility,
   JavaScript, and media-element state.
4. `hybrid_enterprise`: the compatibility schema identifier for an
   instrumented-browser run with explicitly declared task-scoped helper tools.
   This is secondary to the YouTube browser-use tracks.

These classes are never pooled into one leaderboard. Environment stability is
a separate axis: controlled `verified` fixtures versus optional `live`
evaluation.

## Core research questions

1. How much capability is hidden by final-state success alone?
2. Which observation channels improve accuracy, and which merely reduce watch
   cost?
3. Do transcripts improve factual tasks while masking visual-observation
   failures?
4. How often do agents over-watch, under-watch, or select the wrong channel?
5. Does explicit verification reduce transient and persistent disturbance?
6. Can agents maintain correct state across long videos, tabs, and subgoals?
7. How far are agent trajectories from mode-matched human references?
8. Which results transfer from deterministic fixtures to public YouTube pages?

## Intended contribution

The defensible novelty claim is not “the first video-agent benchmark.”
VideoWebArena already evaluates long-context video in agentic workflows, and
LivingScreen evaluates observation control on short-video interfaces.
LongFormMediaBench instead targets the intersection that remains undermeasured:
long-form YouTube browser use where the agent controls temporal observation,
chooses among YouTube-visible and instrumented channels, preserves unrelated
state, and produces verified, timestamp-grounded outcomes.

## Success criterion for the project

The project succeeds when it provides:

- a reproducible local environment and at least 25–50 validated seed tasks;
- versioned task, trace, result, fixture, rubric, and run-manifest contracts;
- human references and interval-level temporal ground truth;
- deterministic evaluators with negative and anti-gaming tests;
- baseline results across separated access classes;
- a redacted aggregate artifact that can regenerate paper tables and figures
  without raw authenticated traces.
