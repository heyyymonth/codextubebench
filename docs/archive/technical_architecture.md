# Archived: Technical Architecture

## Independent axes

Four concepts must not be collapsed:

- benchmark track: deterministic YouTube-like core or live YouTube pilot;
- task family: playback/state, temporal evidence, cross-video, or closed-loop;
- access mode: GUI-native, UI-assisted, instrumented browser, or hybrid;
- agent implementation and configuration.

A run selects exactly one access mode and one environment class. Results from
different access modes or fixture/live environments are never pooled into one
leaderboard.

## Execution flow

```text
task + fixture + access policy + agent config
                    |
                    v
              harness session
                    |
          capability and safety gate
                    |
        observation/action/tool adapters
                    |
          immutable versioned trace
                    |
 pre-state + trajectory + post-state + submission
                    |
         independent evaluator pipeline
                    |
       result vector + aggregate export
```

The agent receives only its instruction and declared authority. Relevant
spans, oracle state, protected invariants, rubrics, and human trajectories are
not exposed to the agent.

## Access modes

| Mode | Available channels |
| --- | --- |
| `gui_native` | Screenshots, recordings, audio playback, pointer, keyboard |
| `ui_assisted` | GUI-native plus normal user-visible transcript, captions, chapters, description, comments, and platform search |
| `instrumented_browser` | UI-assisted plus accessibility tree, DOM, restricted JavaScript, and media-element state |
| `hybrid_enterprise` | Compatibility schema identifier for instrumented browser plus explicitly declared task-scoped helper tools; secondary to the core browser-use tracks |

Every channel request passes through a capability gate. Denied requests become
trace events and affect eligibility; they are not silently discarded.

## Stable repository boundaries

```text
youtube-benchmark/
  benchmarks/
    tubecontrol/
    tubecontrol_executable_v0/
    longform_seed/
  configs/
    modes/
  docs/
  examples/
  schemas/
  src/tubebench/
    catalog.py
    longform_catalog.py
    intervals.py
    temporal_metrics.py
    modes.py
    runner.py
    executable.py
    fixture_server.py
  tests/
```

The stable public repository owns contracts, deterministic evaluators, fixture
specifications, seed task definitions, and reproducible documentation.
Playwright adapters, provider-specific agents, raw traces, and unstable
experiments begin in `youtube-benchmark-lab/`. The paper repository receives
only aggregate redacted bundles.

## Trace model

The YouTube long-form trace envelope requires task revision, access mode,
benchmark Git revision, sequence, timestamp, event type, and payload. Event
types cover:

- task start and end;
- observations and channel access;
- browser actions and tool calls;
- media-watch intervals;
- checkpoints and verification;
- side effects;
- final answers and metric fragments.

Temporal evaluators distinguish:

- unique continuous watched intervals;
- repeated playback exposure;
- point observations such as screenshots;
- transcript or caption cue access;
- player playback that occurred without agent attention.

A seek jump is not watched time. Background playback does not receive
evidence credit unless the task explicitly permits audio-only attention.

## Evaluator boundaries

Evaluators are read-only consumers of immutable trace and oracle snapshots:

- predicate evaluator: exact completion;
- temporal evaluator: interval coverage and localization;
- disturbance evaluator: transient and final protected-state changes;
- channel evaluator: allowed, forbidden, and ineffective channel use;
- verification evaluator: post-action evidence and independence;
- state evaluator: checkpoint correctness;
- efficiency evaluator: human-reference resource ratios;
- rubric evaluator: structured workflow output.

Evaluator code never drives the browser. Browser adapters cannot write result
metrics directly.

## Local fixture

`fixtures/longform_player/` is a YouTube-like, non-branded local browser
surface backed by the same deterministic state machine used for replay scoring.
It currently provides:

- 12 benchmark-authored tasks over 40–60 minute virtual timelines;
- multiple player instances, playback, seek, mute, rate, and watch actions;
- deterministic chapters, transcripts, and visual-only events;
- resettable in-memory sessions;
- mode-filtered agent views;
- a random token-protected oracle and evaluated trace endpoint unavailable to
  the browser page.

Encoded audio/video, multilingual captions, prompt-injection canaries, and
broader YouTube workflow fixtures remain planned expansion work.

## CLI target

The compatibility CLI remains:

```bash
tubebench validate
tubebench validate-longform
tubebench validate-executable
tubebench run --agent mock-perfect --seed 1 --output runs/mock
tubebench run-executable --agent scripted --output runs/executable
tubebench serve-fixture --port 8765
tubebench score-executable-trace trace.json --output evaluated-trace.json
```

Each run must record Git SHA and dirty status, task/fixture/config digests,
schema and evaluator versions, browser/OS state, seed, clock rate, and artifact
checksums.
