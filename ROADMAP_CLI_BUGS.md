# ROADMAP CLI Bugs

Working log of bugs and inconsistencies observed while using the `roadmap` CLI in this repository. Add new findings here as they are discovered.

## 1. Missing Milestone In CLI Index

### Summary

The `sppm-semantic-completeness` milestone existed on disk and its issues were queryable, but the milestone was initially missing from normal CLI milestone views.

### Evidence

- `.roadmap/milestones/sppm-semantic-completeness.md` existed in the repository.
- `roadmap issue list -m sppm-semantic-completeness ...` returned the expected milestone issues.
- `roadmap milestone list` did not include `sppm-semantic-completeness`.
- `roadmap milestone view sppm-semantic-completeness` initially returned `Milestone 'sppm-semantic-completeness' not found.`

### Impact

The CLI can present roadmap data that is inconsistent with the file-backed source of truth. That makes milestone planning and prioritization unreliable.

### Current Workaround

Re-created the milestone through the CLI with `roadmap milestone create ...`, which caused it to appear in subsequent CLI milestone views.

## 2. `roadmap health scan` Internal Failure

### Summary

The health scan command raised internal attribute errors instead of scanning roadmap entities correctly.

### Evidence

Observed errors included:

- `'RoadmapCore' object has no attribute 'issue_repository'`
- `'RoadmapCore' object has no attribute 'milestone_repository'`
- `'RoadmapCore' object has no attribute 'project_repository'`

After logging those errors, the command still reported `No entities to report.`

### Impact

The health scan cannot be trusted to detect roadmap inconsistencies, and the success-like summary is misleading because internal failures occurred.

### Current Workaround

None. Avoid relying on `roadmap health scan` until the command is fixed.

## 3. `roadmap health fix` Crashes During Fix Application

### Summary

The automatic health-fix path failed with a runtime exception instead of applying fixes.

### Evidence

The command failed with:

`OldBackupsFixer.apply() got an unexpected keyword argument 'force'`

### Impact

Automatic repair of roadmap health issues is currently unavailable through the CLI.

### Current Workaround

None through the CLI. Any fixes have to be handled manually or through other commands.

## 4. `roadmap health --details` Help Surface Is Misleading

### Summary

The top-level health help advertises a `--details` option, but that option is not accepted by at least one health subcommand where a user would reasonably expect it to work.

### Evidence

- `roadmap health --help` shows `--details`.
- `roadmap health db-integrity --details` failed with `Error: No such option: --details`.

### Impact

The CLI help surface is confusing and makes it harder to discover the correct invocation pattern for health diagnostics.

### Current Workaround

Use subcommand-specific help and avoid assuming top-level options are inherited by subcommands.

## 5. `roadmap milestone update` Success Message Is Wrong

### Summary

Updating a milestone succeeded, but the CLI printed a malformed success message.

### Evidence

When updating the SPPM milestone, the CLI printed:

`Updated bool: Untitled`

The milestone update itself appeared to apply correctly afterward.

### Impact

The command output is misleading and makes it harder to trust update results during active planning work.

### Current Workaround

Verify milestone state with a follow-up command such as `roadmap milestone view <id>`.

## 6. `roadmap today` Does Not Reliably Reflect Dependency Order

### Summary

The daily summary view updates milestone priority correctly, but its `Up Next` ordering does not appear to consistently reflect the actual dependency chain.

### Evidence

- After moving direct renderer-platform blockers into the SPPM milestone, `roadmap today` correctly switched to `sppm-semantic-completeness (due 2026-05-08)`.
- The `Up Next` list still surfaced standalone SPPM items first rather than the newly moved critical blocker issues that sit on the dependency path for several downstream tasks.

### Impact

The daily queue can steer work toward milestone members that are not the best next task from a dependency perspective.

### Current Workaround

Cross-check `roadmap today` against explicit issue dependencies and critical-path analysis before deciding what to start.

## Notes

This document is intended to be append-only during the current push. New CLI bugs, repro steps, and workarounds should be added here as they are discovered.