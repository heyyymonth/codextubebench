const STATIC_FIXTURE_VERSION = "codextubebench-static-fixture.v0.3";
const STATIC_FIXTURE_ID = "codextubebench-static-tce-002";
const STATIC_ASSET_REVISION = "v0.3-ready";
const SCORER_CONTRACT_VERSION = "codextubebench-static-trace-result.v0.1";
const {
  attemptOptionalTransfer,
  buildSummary,
  finalizeTrace,
  sanitizePublicUrl,
  selectTraceText,
  serializeTrace,
} = CodexTubeBenchStaticTrace;

let fixture = null;
let deployment = null;
let trace = null;
let initialState = null;
let state = null;
let submitted = false;
let controlsAttached = false;
let assetsLoaded = {
  task_json: false,
  trace_template_json: false,
  deployment_metadata_json: false,
  app_js: true,
  trace_handoff_js: true,
};

function now() {
  return new Date().toISOString();
}

function runId() {
  if (typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `static-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formatTime(value) {
  const total = Math.max(0, Math.round(Number(value)));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  const prefix = hours ? `${String(hours).padStart(2, "0")}:` : "";
  return `${prefix}${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function setStatus(message, error = false) {
  const status = document.querySelector("#status");
  status.textContent = message;
  status.className = error ? "status error" : "status success";
}

function traceHandoffReady() {
  return Boolean(
    typeof CodexTubeBenchStaticTrace !== "undefined"
      && CodexTubeBenchStaticTrace
      && typeof finalizeTrace === "function"
      && typeof selectTraceText === "function"
      && typeof serializeTrace === "function",
  );
}

function cockpitControlsAttached() {
  return controlsAttached && [
    "#pause-playing",
    "#final-state-verification",
    "#select-trace",
    "#download-trace",
    "#copy-trace",
  ].every((selector) => Boolean(document.querySelector(selector)));
}

function taskInitialStateRendered() {
  if (!state?.players) {
    return false;
  }
  return document.querySelectorAll("[data-testid^='player-state-player-']").length
    === Object.keys(state.players).length;
}

function readinessChecks() {
  return {
    task_json_loaded: assetsLoaded.task_json,
    trace_template_json_loaded: assetsLoaded.trace_template_json,
    app_js_initialized: true,
    cockpit_controls_attached: cockpitControlsAttached(),
    trace_textarea_exists: Boolean(document.querySelector("#trace-json")),
    static_trace_handoff_ready: traceHandoffReady(),
    task_initial_state_rendered: taskInitialStateRendered(),
  };
}

function publishReadiness({ready, initializedAt = null, error = null, checks = null}) {
  const snapshot = {
    fixture_id: STATIC_FIXTURE_ID,
    fixture_version: STATIC_FIXTURE_VERSION,
    deployed_revision: deployment?.benchmark_git_revision ?? null,
    task_id: fixture?.task?.id ?? "TCE-002",
    assets_loaded: {...assetsLoaded},
    trace_handoff_ready: traceHandoffReady(),
    scorer_contract_version: SCORER_CONTRACT_VERSION,
    initialized_at: initializedAt,
    ready,
    checks: checks ?? readinessChecks(),
    error,
  };
  window.CodexTubeBenchStaticReady = JSON.parse(JSON.stringify(snapshot));

  const indicator = document.querySelector("#fixture-ready");
  if (indicator) {
    indicator.dataset.ready = ready ? "true" : "false";
    indicator.dataset.fixtureId = snapshot.fixture_id;
    indicator.dataset.fixtureVersion = snapshot.fixture_version;
    indicator.dataset.deployedRevision = snapshot.deployed_revision ?? "";
    indicator.dataset.taskId = snapshot.task_id;
    indicator.dataset.assetsLoaded = Object.values(snapshot.assets_loaded).every(Boolean)
      ? "true"
      : "false";
    indicator.dataset.traceHandoffReady = snapshot.trace_handoff_ready ? "true" : "false";
    indicator.dataset.scorerContractVersion = snapshot.scorer_contract_version;
    indicator.textContent = ready
      ? `Readiness: ready · ${snapshot.task_id} · ${snapshot.deployed_revision}`
      : `Readiness: not ready${error ? ` · ${error}` : ""}`;
  }

  const stateNode = document.querySelector("#fixture-readiness-state");
  if (stateNode) {
    stateNode.textContent = JSON.stringify(snapshot, null, 2);
  }
  return snapshot;
}

function markFixtureReady() {
  const checks = readinessChecks();
  const ready = Object.values(checks).every(Boolean);
  publishReadiness({
    ready,
    initializedAt: ready ? now() : null,
    error: ready ? null : "readiness checks incomplete",
    checks,
  });
  return ready;
}

function recordRender(details) {
  trace.observations.push({
    sequence: trace.actions.length,
    channel: "screenshot",
    timestamp: now(),
    details,
  });
}

function playingPlayerId() {
  if (!state) {
    return null;
  }
  const playing = Object.entries(state.players)
    .filter(([, player]) => player.playback === "playing")
    .map(([playerId]) => playerId);
  return playing.length === 1 ? playing[0] : null;
}

function pausePlayer(playerId) {
  if (submitted || !playerId || state.players[playerId].playback !== "playing") {
    return;
  }
  trace.actions.push({type: "pause", player_id: playerId});
  trace.browser_tool_calls.push({
    sequence: trace.actions.length,
    source: "static-browser",
    name: "pause",
    timestamp: now(),
  });
  state.players[playerId].playback = "paused";
  recordRender({post_action_render: true});
  renderCockpitStates();
  renderPlayerDetails();
  const verification = document.querySelector("#final-state-verification");
  verification.disabled = false;
  setStatus(`Recorded pause for ${playerId}. Verify all three states to finalize.`);
}

function pausePlayingPlayer() {
  pausePlayer(playingPlayerId());
}

function renderCockpitStates() {
  const container = document.querySelector("#player-state-list");
  container.replaceChildren();

  for (const [playerId, player] of Object.entries(state.players)) {
    const row = document.createElement("div");
    row.id = `player-state-${playerId}`;
    row.className = "player-state-row";
    row.dataset.testid = `player-state-${playerId}`;

    const identity = document.createElement("span");
    identity.className = "player-identity";
    const id = document.createElement("strong");
    id.textContent = playerId;
    const title = document.createElement("span");
    title.textContent = player.title;
    identity.append(id, title);

    const playback = document.createElement("span");
    playback.className = `state ${player.playback}`;
    playback.dataset.testid = `playback-${playerId}`;
    playback.textContent = player.playback;

    row.append(identity, playback);
    container.append(row);
  }

  const playerId = playingPlayerId();
  const pause = document.querySelector("#pause-playing");
  pause.disabled = submitted || playerId === null;
  pause.textContent = playerId
    ? `Pause ${playerId} — ${state.players[playerId].title}`
    : "Playing player paused";
}

function renderPlayerDetails() {
  const container = document.querySelector("#players");
  container.replaceChildren();

  for (const [playerId, player] of Object.entries(state.players)) {
    const card = document.createElement("article");
    card.className = "player";

    const screen = document.createElement("div");
    screen.className = "screen";
    screen.textContent = "Deterministic long-form frame";

    const heading = document.createElement("div");
    heading.className = "player-heading";
    const headingText = document.createElement("div");
    const eyebrow = document.createElement("p");
    eyebrow.className = "eyebrow";
    eyebrow.textContent = playerId;
    const title = document.createElement("h3");
    title.textContent = player.title;
    headingText.append(eyebrow, title);
    const playback = document.createElement("span");
    playback.className = `state ${player.playback}`;
    playback.textContent = player.playback;
    heading.append(headingText, playback);

    const details = document.createElement("dl");
    for (const [label, value] of [
      ["Time", `${formatTime(player.current_time)} / ${formatTime(player.duration)}`],
      ["Muted", player.muted ? "yes" : "no"],
      ["Speed", `${player.playback_rate}x`],
      ["Chapter", player.chapter_id || "none"],
    ]) {
      const row = document.createElement("div");
      const term = document.createElement("dt");
      term.textContent = label;
      const description = document.createElement("dd");
      description.textContent = value;
      row.append(term, description);
      details.append(row);
    }

    card.append(screen, heading, details);
    container.append(card);
  }
}

function renderSummary(summary) {
  const fields = {
    "#summary-task-id": summary.task_id,
    "#summary-fixture-revision": summary.fixture_revision,
    "#summary-initial-states": summary.initial_states,
    "#summary-final-states": summary.final_states,
    "#summary-action": summary.action_performed,
    "#summary-verification": summary.verification_selected,
    "#summary-timestamp": summary.timestamp,
    "#summary-trace-id": summary.trace_id,
  };
  for (const [selector, value] of Object.entries(fields)) {
    const element = document.querySelector(selector);
    element.textContent = value;
    element.title = value;
  }
}

function finalizeSubmission() {
  if (submitted) {
    return;
  }
  submitted = true;
  trace = finalizeTrace(trace, initialState, state, now());
  const traceText = serializeTrace(trace);
  const textarea = document.querySelector("#trace-json");
  textarea.value = traceText;
  renderSummary(buildSummary(trace, initialState, state));

  document.body.dataset.phase = "completed";
  document.querySelector("#trace-handoff").hidden = false;
  document.querySelector("#submit-answer").textContent = "Blank answer submitted";
  document.querySelector("#submit-answer").disabled = true;
  document.querySelector("#final-state-verification").disabled = true;
  renderCockpitStates();
  setStatus("Trace ready. Select the visible text for the primary manual handoff.");
}

function handleVerificationChange(event) {
  if (event.currentTarget.checked) {
    finalizeSubmission();
  }
}

function selectTrace() {
  if (!submitted) {
    return;
  }
  selectTraceText(document.querySelector("#trace-json"));
  setStatus("Complete trace text selected. Paste it into the private lab trace file.");
}

async function copyTrace() {
  if (!submitted) {
    return;
  }
  const text = document.querySelector("#trace-json").value;
  const result = await attemptOptionalTransfer(
    () => navigator.clipboard.writeText(text),
  );
  if (result.ok) {
    setStatus("Private trace copied. The visible trace remains available.");
  } else {
    setStatus(
      "Clipboard copy was blocked. Use Select trace text for manual handoff.",
      true,
    );
  }
}

async function downloadTrace() {
  if (!submitted) {
    return;
  }
  const text = document.querySelector("#trace-json").value;
  const result = await attemptOptionalTransfer(async () => {
    const blob = new Blob([text], {type: "application/json"});
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${trace.run_id}-trace.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  });
  if (result.ok) {
    setStatus("Download requested. The visible trace remains available.");
  } else {
    setStatus(
      "Download was blocked. Use Select trace text for manual handoff.",
      true,
    );
  }
}

function isInteractiveTarget(target) {
  return target instanceof Element && Boolean(
    target.closest("button, input, select, textarea, a, [contenteditable='true']"),
  );
}

function handleShortcut(event) {
  if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey) {
    return;
  }
  if (isInteractiveTarget(event.target)) {
    return;
  }

  const key = event.key.toLowerCase();
  if (key === "p" || key === " ") {
    event.preventDefault();
    pausePlayingPlayer();
  } else if (key === "v") {
    const verification = document.querySelector("#final-state-verification");
    if (!verification.disabled) {
      verification.checked = true;
      finalizeSubmission();
    }
  } else if (key === "c" && submitted) {
    copyTrace();
  }
}

async function start() {
  try {
    const [taskResponse, templateResponse, deploymentResponse] = await Promise.all([
      fetch(`./task.json?fixture=${STATIC_ASSET_REVISION}`),
      fetch(`./trace-template.json?fixture=${STATIC_ASSET_REVISION}`),
      fetch(`./deployment-metadata.json?fixture=${STATIC_ASSET_REVISION}`),
    ]);
    assetsLoaded = {
      ...assetsLoaded,
      task_json: taskResponse.ok,
      trace_template_json: templateResponse.ok,
      deployment_metadata_json: deploymentResponse.ok,
    };
    if (!taskResponse.ok || !templateResponse.ok || !deploymentResponse.ok) {
      throw new Error("Static fixture assets are incomplete.");
    }
    fixture = await taskResponse.json();
    trace = await templateResponse.json();
    deployment = await deploymentResponse.json();
    initialState = structuredClone(fixture);
    state = structuredClone(fixture);

    const startedAt = now();
    trace.run_id = runId();
    trace.started_at = startedAt;
    trace.ended_at = startedAt;
    trace.benchmark_git_revision = deployment.benchmark_git_revision;
    trace.benchmark_git_dirty = deployment.benchmark_git_dirty;
    trace.execution_surface = {
      type: "manual",
      public_url: sanitizePublicUrl(new URL("./", window.location.href).href),
      fixture_version: STATIC_FIXTURE_VERSION,
      deployment_id: deployment.deployment_id,
    };
    recordRender({
      initial_render: true,
      initial_playback_states: CodexTubeBenchStaticTrace.playbackStates(initialState),
    });

    document.querySelector("#task-mode").textContent = fixture.task.mode;
    document.querySelector("#task-title").textContent =
      `${fixture.task.id}: ${fixture.task.title}`;
    document.querySelector("#task-instruction").textContent =
      fixture.task.instruction;
    document.querySelector("#deployment-meta").textContent =
      `${deployment.deployment_id} · ${deployment.benchmark_git_revision}`;
    renderCockpitStates();
    renderPlayerDetails();
    if (markFixtureReady()) {
      setStatus("Static fixture ready. No task has been scored.");
    } else {
      setStatus("Static fixture loaded but readiness checks are incomplete.", true);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    publishReadiness({
      ready: false,
      error: message,
      checks: readinessChecks(),
    });
    setStatus(message, true);
  }
}

function attachControls() {
  document.querySelector("#pause-playing").addEventListener("click", pausePlayingPlayer);
  document.querySelector("#final-state-verification").addEventListener(
    "change",
    handleVerificationChange,
  );
  document.querySelector("#select-trace").addEventListener("click", selectTrace);
  document.querySelector("#download-trace").addEventListener("click", downloadTrace);
  document.querySelector("#copy-trace").addEventListener("click", copyTrace);
  document.addEventListener("keydown", handleShortcut);
  controlsAttached = true;
}

publishReadiness({ready: false, checks: readinessChecks()});
attachControls();
start();
