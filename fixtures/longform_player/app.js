const params = new URLSearchParams(window.location.search);
const taskId = params.get("task") || "TCE-002";
const mode = params.get("mode") || undefined;
const agent = params.get("agent") || "manual-browser-agent";
const preflightOnly = params.get("preflight") === "1";

let sessionId = null;
let currentView = null;

function formatTime(value) {
  const total = Math.max(0, Math.round(Number(value)));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  const prefix = hours ? `${String(hours).padStart(2, "0")}:` : "";
  return `${prefix}${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: {"Content-Type": "application/json", ...(options.headers || {})},
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `HTTP ${response.status}`);
  }
  return payload;
}

async function sendAction(action) {
  try {
    currentView = await request(`/api/sessions/${sessionId}/actions`, {
      method: "POST",
      body: JSON.stringify(action),
    });
    render(currentView);
    setStatus(`Recorded ${action.type}.`);
  } catch (error) {
    setStatus(error.message, true);
  }
}

function setStatus(message, error = false) {
  const status = document.querySelector("#status");
  status.textContent = message;
  status.className = error ? "error" : "success";
}

function actionButton(label, action, disabled = false) {
  const button = document.createElement("button");
  button.textContent = label;
  button.disabled = disabled;
  button.addEventListener("click", () => sendAction(action));
  return button;
}

function renderPlayers(view) {
  const container = document.querySelector("#players");
  container.replaceChildren();
  const allowed = new Set(view.task.allowed_action_types);
  for (const [playerId, player] of Object.entries(view.players)) {
    const card = document.createElement("article");
    card.className = "player";
    const visual = player.visual_event
      ? `<div class="visual-event">${player.visual_event}</div>`
      : `<div class="visual-placeholder">Deterministic long-form frame</div>`;
    card.innerHTML = `
      <div class="screen">${visual}</div>
      <div class="player-heading">
        <div>
          <p class="eyebrow">${playerId}</p>
          <h3>${player.title}</h3>
        </div>
        <span class="state ${player.playback}">${player.playback}</span>
      </div>
      <dl>
        <div><dt>Time</dt><dd>${formatTime(player.current_time)} / ${formatTime(player.duration)}</dd></div>
        <div><dt>Muted</dt><dd>${player.muted ? "yes" : "no"}</dd></div>
        <div><dt>Speed</dt><dd>${player.playback_rate}x</dd></div>
        <div><dt>Chapter</dt><dd>${player.chapter_id || "none"}</dd></div>
      </dl>
    `;
    const controls = document.createElement("div");
    controls.className = "controls";
    controls.append(
      actionButton("Play", {type: "play", player_id: playerId}, !allowed.has("play")),
      actionButton("Pause", {type: "pause", player_id: playerId}, !allowed.has("pause")),
      actionButton(
        player.muted ? "Unmute" : "Mute",
        {type: "set_muted", player_id: playerId, value: !player.muted},
        !allowed.has("set_muted"),
      ),
      actionButton(
        "Watch 10s",
        {type: "watch", player_id: playerId, seconds: 10},
        !allowed.has("watch"),
      ),
    );
    const seekLabel = document.createElement("label");
    seekLabel.textContent = "Seek seconds";
    const seekInput = document.createElement("input");
    seekInput.type = "number";
    seekInput.min = "0";
    seekInput.max = String(player.duration);
    seekInput.value = String(Math.round(player.current_time));
    const seekButton = document.createElement("button");
    seekButton.textContent = "Seek";
    seekButton.disabled = !allowed.has("seek");
    seekButton.addEventListener("click", () => {
      sendAction({type: "seek", player_id: playerId, seconds: Number(seekInput.value)});
    });
    const rateLabel = document.createElement("label");
    rateLabel.textContent = "Speed";
    const rate = document.createElement("select");
    for (const value of [0.5, 1, 1.5, 2]) {
      const option = document.createElement("option");
      option.value = String(value);
      option.textContent = `${value}x`;
      option.selected = Number(player.playback_rate) === value;
      rate.append(option);
    }
    rate.disabled = !allowed.has("set_rate");
    rate.addEventListener("change", () => {
      sendAction({type: "set_rate", player_id: playerId, value: Number(rate.value)});
    });
    controls.append(seekLabel, seekInput, seekButton, rateLabel, rate);
    card.append(controls);
    container.append(card);
  }
}

function renderEvidence(view) {
  const section = document.querySelector("#evidence-section");
  const container = document.querySelector("#evidence");
  container.replaceChildren();
  const transcripts = view.transcripts || {};
  const chapters = view.chapters || {};
  const mediaIds = new Set([...Object.keys(transcripts), ...Object.keys(chapters)]);
  section.hidden = mediaIds.size === 0;
  for (const mediaId of mediaIds) {
    const card = document.createElement("article");
    card.className = "evidence-card";
    const title = document.createElement("h3");
    title.textContent = mediaId;
    card.append(title);
    for (const chapter of chapters[mediaId] || []) {
      card.append(
        actionButton(
          `Chapter ${formatTime(chapter.start_seconds)} — ${chapter.label}`,
          {type: "observe", channel: "chapters", media_id: mediaId, chapter_id: chapter.id},
        ),
      );
    }
    for (const cue of transcripts[mediaId] || []) {
      const cueRow = document.createElement("button");
      cueRow.className = "cue";
      cueRow.innerHTML = `<strong>${formatTime(cue.start_seconds)}</strong> ${cue.text}`;
      cueRow.addEventListener("click", () => sendAction({
        type: "observe",
        channel: "transcript",
        media_id: mediaId,
        cue_id: cue.id,
      }));
      card.append(cueRow);
    }
    container.append(card);
  }
}

function renderVerifications(view) {
  const fieldset = document.querySelector("#verifications");
  fieldset.replaceChildren();
  const legend = document.createElement("legend");
  legend.textContent = "Verification performed";
  fieldset.append(legend);
  for (const requirement of view.task.verification_requirements) {
    const label = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = requirement;
    label.append(checkbox, document.createTextNode(requirement.replaceAll("_", " ")));
    fieldset.append(label);
  }
}

function renderEventLog(view) {
  const section = document.querySelector("#event-log-section");
  const output = document.querySelector("#event-log");
  if (!view.event_log) {
    section.hidden = true;
    output.textContent = "";
    return;
  }
  section.hidden = false;
  output.textContent = JSON.stringify(view.event_log, null, 2);
}

function render(view) {
  currentView = view;
  document.querySelector("#task-mode").textContent = view.task.mode;
  document.querySelector("#task-title").textContent = `${view.task.id}: ${view.task.title}`;
  document.querySelector("#task-instruction").textContent = view.task.instruction;
  renderPlayers(view);
  renderEvidence(view);
  renderVerifications(view);
  renderEventLog(view);
  const auditSection = document.querySelector("#audit-section");
  auditSection.hidden = !view.audit_log.length;
  document.querySelector("#audit-log").textContent = JSON.stringify(view.audit_log, null, 2);
}

async function start() {
  if (preflightOnly) {
    for (const section of document.querySelectorAll("[data-session-only]")) {
      section.hidden = true;
    }
    const panel = document.querySelector("#preflight-panel");
    panel.hidden = false;
    document.querySelector("#session-meta").textContent =
      "Preflight only — no benchmark session";
    try {
      const [health, catalog] = await Promise.all([
        request("/health"),
        request("/api/catalog"),
      ]);
      const task = catalog.tasks.find((row) => row.id === taskId);
      if (!task) {
        throw new Error(`Task ${taskId} is not exposed by this deployment.`);
      }
      if (mode && !task.supported_modes.includes(mode)) {
        throw new Error(`Task ${taskId} does not support ${mode}.`);
      }
      document.querySelector("#preflight-title").textContent =
        "Fixture preflight ready";
      document.querySelector("#preflight-detail").textContent =
        "Page assets and sanitized deployment metadata loaded. No benchmark session was created.";
      document.querySelector("#preflight-metadata").textContent = JSON.stringify({
        suite: health.suite,
        revision: health.benchmark_git_revision,
        fixture_version: health.fixture_version,
        deployment_id: health.deployment_id,
        catalog_digest: health.catalog_digest,
        task: task.id,
        task_revision: task.revision,
        mode: mode || "default",
      }, null, 2);
      setStatus("Fixture preflight ready");
    } catch (error) {
      document.querySelector("#preflight-title").textContent =
        "Fixture preflight failed";
      document.querySelector("#preflight-detail").textContent = error.message;
      setStatus(error.message, true);
    }
    return;
  }
  try {
    const created = await request("/api/sessions", {
      method: "POST",
      body: JSON.stringify({task_id: taskId, mode, agent}),
    });
    sessionId = created.session_id;
    document.querySelector("#session-meta").textContent = `Session ${sessionId}`;
    const view = await request(created.view_url);
    render(view);
  } catch (error) {
    setStatus(error.message, true);
  }
}

document.querySelector("#submit-answer").addEventListener("click", async () => {
  const verifications = Array.from(
    document.querySelectorAll("#verifications input:checked"),
    (input) => input.value,
  );
  try {
    await request(`/api/sessions/${sessionId}/submit`, {
      method: "POST",
      body: JSON.stringify({
        answer: document.querySelector("#answer").value,
        verifications,
        qualitative_report: {
          evidence_refs: document.querySelector("#evidence-refs").value,
          state_uncertainty: document.querySelector("#state-uncertainty").value || null,
          failure_notes: document.querySelector("#failure-notes").value || null,
          recovery_notes: document.querySelector("#recovery-notes").value || null,
        },
      }),
    });
    setStatus("Answer submitted. The evaluator can now export and score this session.");
  } catch (error) {
    setStatus(error.message, true);
  }
});

start();
