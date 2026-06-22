# Codex Failure Taxonomy

Assign one primary category to each failed or partial Codex run. The primary
category is the earliest decisive failure in the trajectory. Add contributing
categories when later behavior, such as missing verification or overconfidence,
materially worsens the result.

## 1. Task understanding failure

- **Definition:** Codex interprets the requested goal, target, constraint, or
  success condition incorrectly.
- **Example:** Asked to pause only the playing tab, Codex decides to pause every
  YouTube tab.
- **Trace detection:** plan or action targets conflict with the instruction
  before any UI/tool ambiguity occurs.
- **Deterministic fixture:** yes.
- **Live YouTube required:** no.

## 2. Tool discovery failure

- **Definition:** Codex cannot find or invoke an allowed browser capability
  needed for the task.
- **Example:** Codex cannot discover how to obtain a screenshot or open the
  visible transcript control.
- **Trace detection:** repeated unavailable/invalid tool attempts without
  reaching the relevant UI.
- **Deterministic fixture:** partly.
- **Live YouTube required:** sometimes, for real product controls.

## 3. Browser/tab selection failure

- **Definition:** Codex identifies or acts on the wrong tab, window, iframe, or
  player instance.
- **Example:** It pauses a duplicate-title distractor tab.
- **Trace detection:** action target differs from the task-scoped target;
  protected-tab state changes.
- **Deterministic fixture:** yes.
- **Live YouTube required:** no.

## 4. YouTube UI grounding failure

- **Definition:** Codex sees the correct page but mislocates a visible YouTube
  control or content region.
- **Example:** It clicks captions instead of playback speed.
- **Trace detection:** screenshot/UI observation followed by an action on the
  wrong visible control.
- **Deterministic fixture:** partly.
- **Live YouTube required:** useful for real layout drift.

## 5. Media state interpretation failure

- **Definition:** Codex incorrectly infers playing, paused, muted, buffering,
  ended, live, DVR, or current-time state.
- **Example:** It treats a paused pre-roll as the requested video being paused.
- **Trace detection:** claimed state conflicts with evaluator/player-state
  evidence available before the action.
- **Deterministic fixture:** yes for stable states.
- **Live YouTube required:** for ads, live edges, and volatile states.

## 6. Wrong action execution

- **Definition:** Codex understands the goal and target but executes the wrong
  operation or value.
- **Example:** It seeks to 15:00 instead of 50:00.
- **Trace detection:** action type/value conflicts with the declared goal while
  target grounding is otherwise correct.
- **Deterministic fixture:** yes.
- **Live YouTube required:** no.

## 7. Verification failure

- **Definition:** Codex does not perform or record required post-action checks.
- **Example:** It reports that the video is paused without observing the final
  player state.
- **Trace detection:** missing required verification event or unsupported
  completion claim.
- **Deterministic fixture:** yes.
- **Live YouTube required:** no.

## 8. Side-effect failure

- **Definition:** Codex changes protected or unrelated state.
- **Example:** It pauses another YouTube tab before correcting itself.
- **Trace detection:** forbidden/out-of-scope mutation in the action trajectory.
- **Deterministic fixture:** yes.
- **Live YouTube required:** no, though real browser scope is broader.

## 9. State restoration failure

- **Definition:** Codex makes an allowed temporary change but does not return
  required state to its original or requested value.
- **Example:** It changes playback speed to 1.5x and leaves it there.
- **Trace detection:** initial and final snapshots disagree on a
  restoration-required field.
- **Deterministic fixture:** yes.
- **Live YouTube required:** no.

## 10. Timestamp localization failure

- **Definition:** Codex reports or navigates to a timestamp outside the accepted
  evidence interval.
- **Example:** It gives a chapter start rather than the moment the requested
  visual event occurs.
- **Trace detection:** timestamp error exceeds task tolerance.
- **Deterministic fixture:** yes.
- **Live YouTube required:** no.

## 11. Observation strategy failure

- **Definition:** Codex watches too little, too much, or the wrong temporal
  region to support the answer.
- **Example:** It answers after viewing only the title, or watches most of a
  two-hour video for a narrow question.
- **Trace detection:** insufficient evidence coverage, excessive watched
  intervals, repeated unproductive observations, or unsupported final claim.
- **Deterministic fixture:** yes.
- **Live YouTube required:** useful for realistic scale and metadata.

## 12. Transcript/caption misuse

- **Definition:** Codex treats transcript/caption evidence as sufficient when
  the task requires visual/video observation, or misreads unavailable/partial
  text as complete evidence.
- **Example:** It answers a visual demonstration question from transcript text.
- **Trace detection:** evidence channel violates the task's modality
  obligation.
- **Deterministic fixture:** yes.
- **Live YouTube required:** useful for real transcript availability.

## 13. Live-stream volatility

- **Definition:** a moving live edge, DVR window, stream reset, or changing
  player state invalidates Codex's assumptions or action.
- **Example:** A timestamp target moves outside the available DVR range.
- **Trace detection:** task-relevant state changes between observations without
  a corresponding Codex action.
- **Deterministic fixture:** approximate reproduction is possible.
- **Live YouTube required:** yes for discovery.

## 14. Runtime/tool limitation

- **Definition:** the browser controller, runtime, permission boundary, or tool
  fails independently of Codex task reasoning.
- **Example:** screenshot capture or DOM inspection fails at the needed step.
- **Trace detection:** explicit tool error, unavailable capability, timeout, or
  controller disconnect.
- **Deterministic fixture:** partly.
- **Live YouTube required:** no.

## 15. Overconfident final answer

- **Definition:** Codex declares success or gives a definite answer despite
  missing, conflicting, or failed evidence.
- **Example:** It says “done” after a blocked seek operation.
- **Trace detection:** final claim certainty exceeds criterion outcomes,
  verification evidence, or recorded uncertainty.
- **Deterministic fixture:** yes.
- **Live YouTube required:** no.

## Annotation output

Recommended per-attempt fields:

```json
{
  "outcome": "partial",
  "primary_failure_category": "youtube_ui_grounding_failure",
  "contributing_failure_categories": [
    "verification_failure",
    "overconfident_final_answer"
  ],
  "evidence_event_ids": ["obs-3", "action-2", "verify-1"],
  "deterministic_reproduction_candidate": true,
  "review_notes": "Speed menu was mistaken for captions and final state was not checked."
}
```
