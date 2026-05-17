# AGENTS.md

## Read First

- Start with `README.md`, `STATUS.md`, and `ARCHITECTURE.md`, then consult
  `docs/technical-roadmap.md` and `docs/humanoid-platform-evaluation.md` for
  background research.
- `README.zh.md` is the Chinese README. Keep the English and Chinese README files aligned when changing project positioning, status, or roadmap claims.
- This repo is currently in bootstrap/docs-only state. Do not claim a working runtime pipeline, package layout, test command, or CI gate exists until it is added.

## Project Shape

- neodojo converts official instructional movement videos into simulated multi-view teaching playback.
- The intended MVP path is: official video -> GVHMR SMPL-X output -> GMR retargeting -> SMPL-X teaching track plus Unitree G1 visual track -> MuJoCo/Genesis rendering -> Viser UI.
- SMPL-X is the accuracy source for teaching feedback. G1 is a visual and ecosystem track, not the scoring source.
- Avoid RL, sim2real control, text-to-motion generation, or video-diffusion multi-view generation as core MVP work unless the user explicitly changes direction.

## Data And Outputs

- Do not commit raw videos, generated motion files, model checkpoints, rendered videos, logs, or large outputs. `.gitignore` already excludes `data/raw/`, `data/processed/`, `outputs/`, `checkpoints/`, `*.pt`, `*.pkl`, `*.npz`, and video files.
- Treat official instructional videos as licensing-sensitive. Prefer local/user-supplied source video and retargeted non-image artifacts unless rights are confirmed.
- Keep `.claude/` as local agent artifact storage unless the repo policy changes.

## Commands

- No canonical install, test, lint, or build commands exist yet.
- When adding code, add the command surface in the same change: package metadata, scripts or Make targets, focused tests, and README/docs updates.
- Prefer small, reproducible Python entrypoints for pipeline work before adding broad framework structure.

## Verification

- For docs-only changes, check links, headings, and English/Chinese drift where relevant.
- For code changes, run the narrow test for the changed module and any newly introduced project-level command.
- For rendering/UI work, verify actual frames or screenshots instead of relying only on logs.

## Useful Skills

- Use `$intuitive-init` to refresh this agent harness.
- Use `$intuitive-doc` for human-facing documentation structure or drift.
- Use `$intuitive-tests` before broad test-suite design or cleanup.
- Use `$intuitive-flow` when an idea needs shaping before implementation.
- Use `$intuitive-refactor` before large architecture/refactor work.
- Use `$intuitive-reduce-entropy` for periodic repo cleanup.
