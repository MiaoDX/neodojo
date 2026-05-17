# MVP Lint And Build Surface Plan

Status: IMPLEMENTED

## Goal

Add the smallest honest lint/build command surface for the bootstrap Python
package:

```text
make lint
  -> syntax/import bytecode compile check

make build
  -> wheel artifact under ignored outputs/dist

make verify
  -> lint + tests + build + public-demo smoke + non-GPU real/GPU smoke lanes + audit
```

The goal is a reproducible local and CI command surface, not a full static
analysis or release pipeline.

## Dependencies

- Existing `pyproject.toml` package metadata.
- Existing `make test` and public-demo workflow.
- `.gitignore` policy excluding generated `outputs/`.

## Inputs

- Python source under `src/`.
- Unit tests under `tests/`.
- `pyproject.toml` build metadata.

## Outputs

- `make lint`, using `python -m compileall -q src tests`.
- `make build`, using `python -m pip wheel . --wheel-dir outputs/dist`.
- `make verify`, running lint, plan quality checks, tests, wheel build,
  public-demo generation, real-handoff smoke, GPU bundle/archive/probe smoke,
  fixture-only real-artifact intake smoke, and real-conversion completion
  audit.
- CI steps that run lint, plan quality checks, tests, wheel build, and
  public-demo generation.
- README/README.zh/STATUS/AGENTS updates that describe the limited scope.

## Execution Tasks

1. Add local commands.
   - [x] Add `make lint`.
   - [x] Add `make build`.
   - [x] Add `make verify` and `make all`.
   - [x] Keep build artifacts under ignored `outputs/dist`.

2. Wire CI.
   - [x] Run lint before tests.
   - [x] Run wheel build before public-demo generation.

3. Update docs.
   - [x] Document the commands without claiming full static analysis,
     type-checking, release packaging, or production CI coverage.

## Acceptance Evidence

- `make lint` passes locally.
- `make build` produces a wheel under ignored `outputs/dist`.
- `make verify` runs the complete local verification lane, including the
  fixture-only and metadata-only real/GPU smoke targets plus the real-conversion
  audit.
- `make test` and `make demo-public` still pass.
- CI workflow includes lint, plan quality check, unit test, wheel build,
  public-demo generation, artifact upload, and Pages artifact staging.

## Non-Goals

- Adding Ruff, mypy, pyright, coverage gates, or broad test matrix coverage.
- Publishing a package release.
- Treating syntax lint as proof of runtime correctness.
- Changing the generated-output policy.

## Stop Condition

Stopped when the repo has a minimal verified lint/build surface that can run
locally and in CI without tracking generated build artifacts.
