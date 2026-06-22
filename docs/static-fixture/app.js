const STATIC_FIXTURE_VERSION = "codextubebench-static-fixture.v0.2";

let fixture = null;
let deployment = null;
let trace = null;
let state = null;
let submitted = false;

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
  setStatus(`Recorded pause for ${playerId}. Verify all three states.`);
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

function submitTrace() {
  if (submitted) {
    return;
  }
  submitted = true;
  trace.ended_at = now();
  trace.verifications = document.querySelector("#final-state-verification").checked
    ? ["final_playback_state"]
    : [];
  trace.final_answer = "";
  document.querySelector("#submit-answer").disabled = true;
  document.querySelector("#final-state-verification").disabled = true;
  document.querySelector("#download-trace").disabled = false;
  document.querySelector("#copy-trace").disabled = false;
  renderCockpitStates();
  renderPlayerDetails();
  setStatus("Submitted without scoring. Copy or download the private trace.");
}

function downloadTrace() {
  if (!submitted) {
    return;
  }
  const blob = new Blob(
    [`${JSON.stringify(trace, null, 2)}\n`],
    {type: "application/json"},
  );
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${trace.run_id}-trace.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

async function copyTrace() {
  if (!submitted) {
    return;
  }
  try {
    await navigator.clipboard.writeText(`${JSON.stringify(trace, null, 2)}\n`);
    setStatus("Private trace copied for evaluator review.");
  } catch (error) {
    setStatus("Could not copy the private trace. Use download instead.", true);
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
      verification.checked = !verification.checked;
      setStatus(
        verification.checked
          ? "Final playback state marked verified."
          : "Final playback state verification cleared.",
      );
    }
  } else if (key === "c" && !document.querySelector("#copy-trace").disabled) {
    copyTrace();
  }
}

async function start() {
  try {
    const [taskResponse, templateResponse, deploymentResponse] = await Promise.all([
      fetch("./task.json"),
      fetch("./trace-template.json"),
      fetch("./deployment-metadata.json"),
    ]);
    if (!taskResponse.ok || !templateResponse.ok || !deploymentResponse.ok) {
      throw new Error("Static fixture assets are incomplete.");
    }
    fixture = await taskResponse.json();
    trace = await templateResponse.json();
    deployment = await deploymentResponse.json();
    state = structuredClone(fixture);

    const startedAt = now();
    trace.run_id = runId();
    trace.started_at = startedAt;
    trace.ended_at = startedAt;
    trace.benchmark_git_revision = deployment.benchmark_git_revision;
    trace.benchmark_git_dirty = deployment.benchmark_git_dirty;
    trace.execution_surface = {
      type: "manual",
      public_url: new URL("./", window.location.href).href,
      fixture_version: STATIC_FIXTURE_VERSION,
      deployment_id: deployment.deployment_id,
    };
    recordRender({initial_render: true});

    document.querySelector("#task-mode").textContent = fixture.task.mode;
    document.querySelector("#task-title").textContent =
      `${fixture.task.id}: ${fixture.task.title}`;
    document.querySelector("#task-instruction").textContent =
      fixture.task.instruction;
    document.querySelector("#deployment-meta").textContent =
      `${deployment.deployment_id} · ${deployment.benchmark_git_revision}`;
    renderCockpitStates();
    renderPlayerDetails();
    setStatus("Static fixture ready. No task has been scored.");
  } catch (error) {
    setStatus(error.message, true);
  }
}

document.querySelector("#pause-playing").addEventListener("click", pausePlayingPlayer);
document.querySelector("#submit-answer").addEventListener("click", submitTrace);
document.querySelector("#download-trace").addEventListener("click", downloadTrace);
document.querySelector("#copy-trace").addEventListener("click", copyTrace);
document.addEventListener("keydown", handleShortcut);

start();
