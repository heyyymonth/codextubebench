"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const {
  attemptOptionalTransfer,
  buildSummary,
  finalizeTrace,
  sanitizePublicUrl,
  selectTraceText,
  serializeTrace,
} = require("../docs/static-fixture/trace-handoff.js");

function traceTemplate() {
  return {
    schema_version: "tubecontrol-executable-trace.v0.1",
    run_id: "trace-test",
    task_id: "TCE-002",
    task_revision: 1,
    mode: "gui_native",
    agent: "codex-static-pages-smoke",
    execution_surface: {
      type: "manual",
      public_url: "https://example.test/fixture/",
      fixture_version: "codextubebench-static-fixture.v0.3",
      deployment_id: "test-deployment",
    },
    benchmark_git_revision: "abc123",
    benchmark_git_dirty: false,
    started_at: "2026-06-23T00:00:00.000Z",
    ended_at: "2026-06-23T00:00:00.000Z",
    observations: [],
    screenshots: [],
    actions: [{type: "pause", player_id: "player-b"}],
    browser_tool_calls: [],
    watched_intervals: [],
    transcript_cues_used: [],
    chapter_ids_used: [],
    dom_player_state_reads: [],
    verifications: [],
    final_answer: "",
    final_oracle_state: {},
    side_effects: {},
    metrics: {},
    passed: false,
    errors: [],
  };
}

const initialState = {
  players: {
    "player-a": {playback: "paused"},
    "player-b": {playback: "playing"},
    "player-c": {playback: "paused"},
  },
};
const finalState = {
  players: {
    "player-a": {playback: "paused"},
    "player-b": {playback: "paused"},
    "player-c": {playback: "paused"},
  },
};

test("finalization populates valid trace JSON exactly once", () => {
  const timestamp = "2026-06-23T00:00:01.000Z";
  const finalized = finalizeTrace(
    traceTemplate(),
    initialState,
    finalState,
    timestamp,
  );
  const second = finalizeTrace(finalized, initialState, finalState, timestamp);
  const parsed = JSON.parse(serializeTrace(second));

  assert.equal(parsed.ended_at, timestamp);
  assert.deepEqual(parsed.verifications, ["final_playback_state"]);
  assert.equal(parsed.final_answer, "");
  assert.equal(parsed.observations.length, 1);
  assert.equal(parsed.browser_tool_calls.length, 1);
  assert.deepEqual(
    parsed.observations[0].details.final_playback_states,
    {
      "player-a": "paused",
      "player-b": "paused",
      "player-c": "paused",
    },
  );
});

test("summary includes all manual-ingestion fields", () => {
  const finalized = finalizeTrace(
    traceTemplate(),
    initialState,
    finalState,
    "2026-06-23T00:00:01.000Z",
  );
  assert.deepEqual(buildSummary(finalized, initialState, finalState), {
    task_id: "TCE-002",
    fixture_revision: "abc123",
    initial_states: "a: paused · b: playing · c: paused",
    final_states: "a: paused · b: paused · c: paused",
    action_performed: "pause player-b",
    verification_selected: "yes",
    timestamp: "2026-06-23T00:00:01.000Z",
    trace_id: "trace-test",
  });
});

test("select trace text focuses and selects the complete value", () => {
  const calls = [];
  const textarea = {
    value: "complete trace",
    focus() {
      calls.push("focus");
    },
    select() {
      calls.push("select");
    },
    setSelectionRange(start, end) {
      calls.push([start, end]);
    },
  };
  selectTraceText(textarea);
  assert.deepEqual(calls, ["focus", "select", [0, 14]]);
});

test("clipboard and download failures remain optional", async () => {
  const clipboard = await attemptOptionalTransfer(async () => {
    throw new Error("clipboard denied");
  });
  const download = await attemptOptionalTransfer(async () => {
    throw new Error("download blocked");
  });
  assert.equal(clipboard.ok, false);
  assert.equal(download.ok, false);
  assert.match(clipboard.error, /clipboard denied/);
  assert.match(download.error, /download blocked/);
});

test("public URL sanitizer removes credentials, query, and fragment", () => {
  assert.equal(
    sanitizePublicUrl("https://user:pass@example.test/fixture/?token=secret#private"),
    "https://example.test/fixture/",
  );
});
