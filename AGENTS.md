# AGENTS.md

## Read First

- Start with `README.md`, `STATUS.md`, and `ARCHITECTURE.md`, then consult
  `docs/technical-roadmap.md` and `docs/humanoid-platform-evaluation.md` for
  background research.
- `README.zh.md` is the Chinese README. Keep the English and Chinese README files aligned when changing project positioning, status, or roadmap claims.
- This repo is currently in bootstrap state with a fixture-only HTML demo. Do not claim a working GVHMR/GMR/simulator runtime pipeline, install workflow, lint command, build command, or CI gate exists until it is added.

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

- `make test` runs the focused unit tests for the fixture demo generator, local motion contract, G1 visual-track manifest boundary, local G1 render evidence, and teaching playback manifest path.
- `PYTHONPATH=src python -m neodojo motion-record create --out outputs/motion-contract` writes fixture-backed SMPL-X motion-record and teaching-track manifests.
- `PYTHONPATH=src python -m neodojo motion-record create --from-gvhmr-json path/to/gvhmr-smplx-joints.json --out outputs/motion-contract` imports an external GVHMR SMPL-X teaching-joints JSON export into the same motion-record contract without running GVHMR locally.
- `PYTHONPATH=src python -m neodojo robot-model register --robot unitree_g1 --fixture --out outputs/g1-visual` writes a fixture G1 model descriptor.
- `PYTHONPATH=src python -m neodojo tracks build --motion-record outputs/motion-contract --robot unitree_g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --out outputs/g1-visual` writes a fixture-derived G1 visual-track manifest and comparison report.
- `PYTHONPATH=src python -m neodojo render g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --g1-track outputs/g1-visual/tracks/g1/manifest.json --allow-fixture-model --out outputs/g1-render` writes local SVG/HTML G1 render evidence and a render manifest from the descriptor and visual track; this is not MuJoCo/Genesis mesh rendering.
- `PYTHONPATH=src python -m neodojo demo play --motion-record outputs/motion-contract --g1-track outputs/g1-visual/tracks/g1/manifest.json --out outputs/teaching-demo` writes a fixture-only teaching playback HTML and manifest from the SMPL-X and G1 manifests; optional `--reference-video` preserves local-only original-video sync metadata.
- `PYTHONPATH=src python -m neodojo demo export-rerun --playback outputs/teaching-demo/manifest.json --g1-render outputs/g1-render/manifest.json --out outputs/public-demo/neodojo-demo.rrd` writes a fixture-only static public-demo HTML page, scene/timeline contract, SVG screenshot, public-demo manifest, and `.rrd`-named JSON fallback artifact.
- `PYTHONPATH=src python -m neodojo real-conversion prepare --id 03-006 --start 0 --end 12 --out outputs/real-conversion-gate` writes ignored source/trim metadata for the later GPU gate without downloading video or running GVHMR.
- `make demo-html` writes the self-contained fixture demo to `outputs/html-demo/index.html` plus the local motion/track manifests it consumes.
- No canonical install, lint, build, or CI commands exist yet.
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
