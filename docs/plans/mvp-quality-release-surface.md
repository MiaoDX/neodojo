# MVP Quality And Release Surface Plan

Status: IMPLEMENTED FIRST QUALITY GATE

## Goal

Move beyond the minimal `compileall` lint and wheel build into a modest quality
surface appropriate for the growing package:

```text
make verify
  -> syntax lint
  -> unit tests
  -> wheel build
  -> public-demo smoke
  -> type/static/coverage checks as they become useful
```

This should raise confidence without pretending the project has a production CI
gate before the checks actually run.

## Dependencies

- [mvp-lint-build-surface.md](mvp-lint-build-surface.md) provides the current
  minimal `make lint`, `make build`, and `make verify` surface.
- [mvp-devex-ci-surface.md](mvp-devex-ci-surface.md) wires the fixture demo lane
  through GitHub Actions.

## Inputs

- Existing Python package and tests.
- Candidate tooling such as ruff, pyright/mypy, coverage.py, or pytest.
- CI runtime and cache constraints.

## Outputs

- `make check`, backed by `neodojo quality check`.
- MVP plan-link and plan-scaffold verification.
- CI steps matching local commands.
- Coverage or type reports when useful.
- Documentation that names exactly which quality gates exist.

## Execution Tasks

1. Select smallest useful check.
   - [x] Prefer checks that catch real bugs in the current package.
   - [x] Avoid heavyweight dependencies until the codebase needs them.

2. Add local command.
   - [x] Add package metadata/dependency configuration.
   - [x] Add Make target and focused tests/fixtures if needed.

3. Wire CI and docs.
   - [x] Run the same command in GitHub Actions.
   - [x] Update README, README.zh.md, STATUS, and this plan.

## Acceptance Evidence

- Each claimed quality command runs locally and in CI.
- `make verify` remains the all-in-one local command.
- Generated reports and caches stay ignored.
- Docs do not overstate install, lint, build, release, or CI maturity.
- `make check` runs `neodojo quality check`, verifying MVP plan links and
  minimum plan scaffolding with no third-party dependency.

## Non-Goals

- Broad release automation before a real package release is needed.
- Requiring GPU, source videos, simulator assets, or browser dependencies for
  every CI run.
- Replacing focused unit tests with only static checks.

## Stop Condition

Stopped when the next useful quality gate is added, documented, and included in
`make verify`, or when the current minimal surface remains sufficient and the
decision is recorded.
