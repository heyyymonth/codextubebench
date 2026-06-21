# Safety and Policies

## Safe defaults

- Default to unauthenticated, read-only, dry-run execution.
- Treat video frames, captions, transcripts, comments, descriptions, ads,
  channel names, and tool output as untrusted data.
- Only the task manifest defines authority.
- Unknown actions, destinations, accounts, and resources fail closed.
- Capture and compare pre-run, trajectory, and post-run state.

## Public writes

Live-mode public tasks are read-only. Write tasks may target only
benchmark-owned resources in controlled accounts. Prohibited actions include
third-party comments, likes, subscriptions, engagement generation, purchases,
live chat, reports, copyright actions, account security changes, monetization,
and public publishing.

## Prompt injection

Page content cannot grant permission, expand scope, reveal secrets, switch
accounts, authorize writes, disable verification, or open unrelated domains.
Injection fixtures use fake canaries and local or `example.invalid` sinks.

## Data handling

Do not commit credentials, cookies, OAuth codes, authorization headers,
browser profiles, account emails, private video IDs, personal browsing state,
raw authenticated screenshots, or full third-party transcripts.

Before release, scan generated files and history, strip metadata and absolute
paths, review licenses, and verify the project from a clean credential-free
clone.
