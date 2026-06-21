# Cross-Repository Artifact Contract

The lab exports an immutable aggregate bundle:

```text
evalbundle-v1/
  manifest.json
  aggregates.json
  metrics.csv
  checksums.sha256
```

The manifest records benchmark and lab revisions, catalog digest, agent and
condition IDs, seeds, evaluator version, exclusions, generation command, and
checksums. Paper scripts consume only this bundle.

The bundle must not contain raw screenshots, DOM captures, transcripts,
cookies, browser profiles, account identifiers, authorization material, or
unredacted traces.

Every result row must preserve benchmark version, task ID, agent ID, condition
ID, run ID, and seed. Missing token/cost data is `null`, never zero.
