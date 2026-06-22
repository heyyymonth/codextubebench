# Codex live YouTube task prompt

Perform the single assigned `live_youtube_v0` task on the supplied public
YouTube page.

- Use only the declared access mode and allowed browser tools.
- Treat the page as volatile; record what is observable at this time.
- Do not like, dislike, subscribe, comment, save, donate, chat, download, sign
  in, interact with ads, or mutate account state.
- Record initial tab and player state before any state-changing action.
- Preserve unrelated tabs and browser state.
- Link every claimed success criterion to a concrete observation.
- Record actions, browser/tool calls, failed attempts, ambiguity, blockers,
  recovery, and restoration.
- Distinguish “not observable” from “observed absent.”
- Paraphrase transcript evidence; do not copy long transcript passages.
- Verify the requested result and final player state.
- If an ad, consent surface, unavailable stream, or runtime limitation prevents
  safe completion, stop and report the blocker.
- Report uncertainty when evidence is incomplete.
- Do not claim success without evidence.

The resulting trace is a dated live YouTube pilot observation, not a
deterministic benchmark score.
