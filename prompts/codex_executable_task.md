# Codex deterministic-task prompt

Perform the single YouTube-like browser task shown in the CodexTubeBench local
fixture.

- Use only the interaction channels allowed by the declared mode.
- Do not inspect benchmark source, expected answers, evaluator state, scripted
  actions, or oracle endpoints.
- Record observations and actions through the supplied browser interface.
- Before changing state, verify the intended tab/player and protected state.
- Make only the changes required by the task.
- After acting, verify the requested final state or answer using allowed
  evidence.
- If state is ambiguous, investigate or report uncertainty; do not guess.
- Do not claim success without supporting final-state evidence.
- Submit the final answer through the page. Leave it blank for state-only tasks.
