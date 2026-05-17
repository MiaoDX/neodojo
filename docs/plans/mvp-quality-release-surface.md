# MVP Quality And Release Surface Plan

Status: PLANNED

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

- Additional Make targets only after their tools are added.
- CI steps matching local commands.
- Coverage or type reports when useful.
- Documentation that names exactly which quality gates exist.

## Execution Tasks

1. Select smallest useful check.
   - [ ] Prefer checks that catch real bugs in the current package.
   - [ ] Avoid heavyweight dependencies until the codebase needs them.

2. Add local command.
   - [ ] Add package metadata/dependency configuration.
   - [ ] Add Make target and focused tests/fixtures if needed.

3. Wire CI and docs.
   - [ ] Run the same command in GitHub Actions.
   - [ ] Update README, README.zh.md, STATUS, and this plan.

## Acceptance Evidence

- Each claimed quality command runs locally and in CI.
- `make verify` remains the all-in-one local command.
- Generated reports and caches stay ignored.
- Docs do not overstate install, lint, build, release, or CI maturity.

## Non-Goals

- Broad release automation before a real package release is needed.
- Requiring GPU, source videos, simulator assets, or browser dependencies for
  every CI run.
- Replacing focused unit tests with only static checks.

## Stop Condition

Stop when the next useful quality gate is added, documented, and included in
`make verify`, or when the current minimal surface remains sufficient and the
decision is recorded.
