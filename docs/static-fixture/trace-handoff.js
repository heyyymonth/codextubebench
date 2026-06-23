(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.CodexTubeBenchStaticTrace = api;
}(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  function clone(value) {
    if (typeof structuredClone === "function") {
      return structuredClone(value);
    }
    return JSON.parse(JSON.stringify(value));
  }

  function sanitizePublicUrl(value) {
    const url = new URL(value);
    if (!["http:", "https:"].includes(url.protocol)) {
      throw new Error("Static fixture URL must use HTTP or HTTPS.");
    }
    url.username = "";
    url.password = "";
    url.search = "";
    url.hash = "";
    return url.href;
  }

  function playbackStates(state) {
    return Object.fromEntries(
      Object.entries(state.players).map(([playerId, player]) => [
        playerId,
        player.playback,
      ]),
    );
  }

  function summarizeStates(states) {
    return Object.entries(states)
      .map(([playerId, playback]) => `${playerId.replace("player-", "")}: ${playback}`)
      .join(" · ");
  }

  function finalizeTrace(trace, initialState, finalState, timestamp) {
    const finalized = clone(trace);
    const completionExists = finalized.observations.some(
      (observation) => observation.details?.static_trace_completion === true,
    );
    if (completionExists) {
      return finalized;
    }

    const initialPlaybackStates = playbackStates(initialState);
    const finalPlaybackStates = playbackStates(finalState);
    finalized.ended_at = timestamp;
    finalized.verifications = ["final_playback_state"];
    finalized.final_answer = "";
    finalized.observations.push({
      sequence: finalized.actions.length,
      channel: "player_state",
      timestamp,
      details: {
        static_trace_completion: true,
        initial_playback_states: initialPlaybackStates,
        final_playback_states: finalPlaybackStates,
        verification: "final_playback_state",
      },
    });
    finalized.browser_tool_calls.push({
      sequence: finalized.actions.length + 1,
      source: "static-browser",
      name: "verify_final_playback_state",
      timestamp,
    });
    return finalized;
  }

  function buildSummary(trace, initialState, finalState) {
    const action = trace.actions.length === 1
      ? `${trace.actions[0].type} ${trace.actions[0].player_id}`
      : `${trace.actions.length} actions`;
    return {
      task_id: trace.task_id,
      fixture_revision: trace.benchmark_git_revision,
      initial_states: summarizeStates(playbackStates(initialState)),
      final_states: summarizeStates(playbackStates(finalState)),
      action_performed: action,
      verification_selected: trace.verifications.includes("final_playback_state")
        ? "yes"
        : "no",
      timestamp: trace.ended_at,
      trace_id: trace.run_id,
    };
  }

  function serializeTrace(trace) {
    return `${JSON.stringify(trace, null, 2)}\n`;
  }

  function selectTraceText(textarea) {
    textarea.focus();
    textarea.select();
    if (typeof textarea.setSelectionRange === "function") {
      textarea.setSelectionRange(0, textarea.value.length);
    }
  }

  async function attemptOptionalTransfer(operation) {
    try {
      await operation();
      return {ok: true, error: null};
    } catch (error) {
      return {
        ok: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  return {
    attemptOptionalTransfer,
    buildSummary,
    finalizeTrace,
    playbackStates,
    sanitizePublicUrl,
    selectTraceText,
    serializeTrace,
    summarizeStates,
  };
}));
