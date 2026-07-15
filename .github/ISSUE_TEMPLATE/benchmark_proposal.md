---
name: Benchmark proposal
about: Propose a task, failure reproduction, predicate, or protocol change
title: "[Proposal] "
labels: ""
assignees: ""
---

## Proposal

Describe the task, failure, evaluator gap, or protocol change and why it belongs
in TubeBench.

## Track and evidence class

- Proposed track: deterministic fixture / live YouTube / live public video
- Intended evidence label: design / diagnostic / protocol validation / dated pilot
- Access mode: GUI-native / UI-assisted / instrumented browser / hybrid

## Task contract

- Objective and user-visible instruction:
- Target disambiguation:
- Initial state or public-page preconditions:
- Allowed actions:
- Forbidden actions:
- Exact success predicates:
- Protected state and side-effect predicates:
- Required evidence channels:
- Verification requirements:
- Failure categories exercised:

## Fixture or public source

For fixtures, describe deterministic reset, evaluator authority, media
ownership, license, and publication permission. For public pages, explain why
the task is read-only, unauthenticated, and safe under page volatility.

## Evaluation and tests

Describe the reference trajectory, step budget, positive and negative evaluator tests,
expected failure reproduction, and repeated validation plan.

## Paper and experiment relevance

State which current claim, metric, failure, or experimental setup this proposal
supports. Do not claim model performance without reviewed aggregate evidence.

## Privacy and safety check

- [ ] The proposal contains no credentials, tokens, cookies, profiles, account
      identifiers, raw private traces, authenticated captures, or full
      third-party transcripts.
- [ ] Public live behavior is read-only and does not include likes, comments,
      subscriptions, downloads, purchases, chat, ad interaction, or login.
- [ ] All write actions use benchmark-owned fixtures.
- [ ] Evidence can be shared as synthetic examples or reviewed aggregates.
