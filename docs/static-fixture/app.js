const STATIC_FIXTURE_VERSION = "codextubebench-static-fixture.v0.1";

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
  status.className = error ? "error" : "success";
}

function recordRender(details) {
  trace.observations.push({
    sequence: trace.actions.length,
    channel: "screenshot",
    timestamp: now(),
    details,
  });
}

function pausePlayer(playerId) {
  if (submitted) {
    return;
  }
  const action = {type: "pause", player_id: playerId};
  trace.actions.push(action);
  trace.browser_tool_calls.push({
    sequence: trace.actions.length,
    source: "static-browser",
    name: "pause",
    timestamp: now(),
  });
  state.players[playerId].playback = "paused";
  recordRender({post_action_render: true});
  renderPlayers();
  setStatus(`Recorded pause for ${playerId}.`);
}

function renderPlayers() {
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

    const controls = document.createElement("div");
    controls.className = "controls";
    const pause = document.createElement("button");
    pause.textContent = "Pause";
    pause.disabled = submitted || player.playback === "paused";
    pause.addEventListener("click", () => pausePlayer(playerId));
    controls.append(pause);
    card.append(screen, heading, details, controls);
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
  renderPlayers();
  setStatus("Submitted without scoring. Export the private trace for evaluator review.");
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
    setStatus("Could not copy the private trace. Use the download control instead.", true);
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
    renderPlayers();
    setStatus("Static fixture ready. No task has been scored.");
  } catch (error) {
    setStatus(error.message, true);
  }
}

document.querySelector("#submit-answer").addEventListener("click", submitTrace);
document.querySelector("#download-trace").addEventListener("click", downloadTrace);
document.querySelector("#copy-trace").addEventListener("click", copyTrace);

start();
