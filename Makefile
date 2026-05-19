.PHONY: all verify verify-real lint check test build demo-html demo-public demo-public-browser real-gpu-prep gvhmr-inspect demo-real mujoco-backend-compare real-artifact-intake real-conversion-audit real-conversion-audit-strict smoke-public

PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
REAL_SOURCE_ID ?= 03-006
REAL_START ?= 0
REAL_END ?= 12
REAL_PREP_OUT ?= outputs/real-conversion-gate
REAL_SOURCE_OUT ?= outputs/real-conversion-source
REAL_GPU_RUN_OUT ?= outputs/gvhmr-local-gpu-run
REAL_DRY_RUN ?= 1
GVHMR_INSPECT_OUT ?= outputs/gvhmr-result-inspection
REAL_DEMO_OUT ?= outputs/real-demo
REAL_ARTIFACT_SOURCE_MATERIALIZATION ?= outputs/real-conversion-source/source-materialization.json
REAL_ARTIFACT_GVHMR_JSON ?= outputs/real-conversion-gate/gvhmr-smplx-joints.json
REAL_ARTIFACT_OUT ?= outputs/real-demo
MUJOCO_COMPARE_BACKENDS ?= egl glfw osmesa
MUJOCO_COMPARE_WIDTH ?= 1280
MUJOCO_COMPARE_HEIGHT ?= 960
MUJOCO_COMPARE_OUT ?= outputs/g1-mujoco-backend-comparison
REAL_ARTIFACT_SMOKE_INPUT_OUT ?= outputs/real-artifact-intake-smoke-input
REAL_ARTIFACT_SMOKE_OUT ?= outputs/real-artifact-intake-smoke
REAL_CONVERSION_AUDIT_OUT ?= outputs/real-conversion-audit
REAL_CONVERSION_AUDIT_ARGS = \
	--source-materialization "$(REAL_ARTIFACT_SOURCE_MATERIALIZATION)" \
	--gvhmr-json "$(REAL_ARTIFACT_GVHMR_JSON)" \
	--real-demo "$(REAL_ARTIFACT_OUT)" \
	--out "$(REAL_CONVERSION_AUDIT_OUT)"
REAL_DEMO_ARGS = --source-materialization "$(SOURCE_MATERIALIZATION)" --gvhmr-json "$(GVHMR_JSON)" --out "$(REAL_DEMO_OUT)"
ifdef G1_TRACK
REAL_DEMO_ARGS += --g1-track "$(G1_TRACK)"
endif
ifdef MODEL_DESCRIPTOR
REAL_DEMO_ARGS += --model-descriptor "$(MODEL_DESCRIPTOR)"
endif
ifdef G1_RENDER
REAL_DEMO_ARGS += --g1-render "$(G1_RENDER)"
endif
ifdef RENDER_MUJOCO
REAL_DEMO_ARGS += --render-mujoco
endif
ifdef USE_RERUN_SDK
REAL_DEMO_ARGS += --use-rerun-sdk
endif
ifeq ($(REAL_DRY_RUN),0)
REAL_MATERIALIZE_FLAGS =
else
REAL_MATERIALIZE_FLAGS = --dry-run
endif
REAL_PREP_SOURCE_ARGS = --id "$(REAL_SOURCE_ID)"
ifdef REAL_LOCAL_SOURCE_ID
REAL_PREP_SOURCE_ARGS = --local-source-id "$(REAL_LOCAL_SOURCE_ID)"
endif
ifdef REAL_LOCAL_TITLE
REAL_PREP_SOURCE_ARGS += --local-title "$(REAL_LOCAL_TITLE)"
endif
ifdef REAL_LOCAL_TITLE_CHINESE
REAL_PREP_SOURCE_ARGS += --local-title-chinese "$(REAL_LOCAL_TITLE_CHINESE)"
endif
ifdef REAL_LOCAL_CATEGORY
REAL_PREP_SOURCE_ARGS += --local-category "$(REAL_LOCAL_CATEGORY)"
endif
ifdef REAL_LOCAL_CATEGORY_CHINESE
REAL_PREP_SOURCE_ARGS += --local-category-chinese "$(REAL_LOCAL_CATEGORY_CHINESE)"
endif
ifdef REAL_LOCAL_ORIGIN_URL
REAL_PREP_SOURCE_ARGS += --local-origin-url "$(REAL_LOCAL_ORIGIN_URL)"
endif
ifdef REAL_RIGHTS_NOTES
REAL_PREP_SOURCE_ARGS += --rights-notes "$(REAL_RIGHTS_NOTES)"
endif

all: verify

verify: lint check test build demo-public .real-gpu-prep-smoke .real-artifact-intake-smoke real-conversion-audit

verify-real: real-conversion-audit-strict

lint:
	PYTHONPATH=src $(PYTHON) -m compileall -q src tests

check:
	PYTHONPATH=src $(PYTHON) -m neodojo quality check --repo-root .

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests

build:
	$(PYTHON) -m pip wheel . --wheel-dir outputs/dist

demo-html:
	PYTHONPATH=src $(PYTHON) -m neodojo demo-html --out outputs/html-demo

demo-public:
	rm -rf outputs/motion-contract outputs/smplx-surface outputs/annotations outputs/g1-visual outputs/g1-render outputs/teaching-demo outputs/public-demo outputs/viser-runtime outputs/browser-capture outputs/capture
	PYTHONPATH=src $(PYTHON) -m neodojo motion-record create --out outputs/motion-contract
	PYTHONPATH=src $(PYTHON) -m neodojo smplx-surface proxy --motion-record outputs/motion-contract --out outputs/smplx-surface
	PYTHONPATH=src $(PYTHON) -m neodojo annotations detect --motion-record outputs/motion-contract --out outputs/annotations
	PYTHONPATH=src $(PYTHON) -m neodojo robot-model register --robot unitree_g1 --fixture --out outputs/g1-visual
	PYTHONPATH=src $(PYTHON) -m neodojo tracks build --motion-record outputs/motion-contract --robot unitree_g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --out outputs/g1-visual
	PYTHONPATH=src $(PYTHON) -m neodojo render g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --g1-track outputs/g1-visual/tracks/g1/manifest.json --allow-fixture-model --out outputs/g1-render
	PYTHONPATH=src $(PYTHON) -m neodojo demo play --motion-record outputs/motion-contract --g1-track outputs/g1-visual/tracks/g1/manifest.json --annotations outputs/annotations/manifest.json --smplx-surface outputs/smplx-surface/surfaces/smplx/manifest.json --out outputs/teaching-demo
	PYTHONPATH=src $(PYTHON) -m neodojo demo export-rerun --playback outputs/teaching-demo/manifest.json --g1-render outputs/g1-render/manifest.json --out outputs/public-demo/neodojo-demo.rrd
	PYTHONPATH=src $(PYTHON) -m neodojo demo serve-viser --write-contract-only --playback outputs/teaching-demo/manifest.json --g1-render outputs/g1-render/manifest.json --out outputs/viser-runtime
	PYTHONPATH=src $(PYTHON) -m neodojo demo smoke --public-demo outputs/public-demo
	PYTHONPATH=src $(PYTHON) -m neodojo capture bundle --public-demo outputs/public-demo --viser-runtime outputs/viser-runtime --g1-render outputs/g1-render --out outputs/capture

demo-public-browser: demo-public
	rm -rf outputs/browser-capture
	PYTHONPATH=src $(PYTHON) -m neodojo demo browser-smoke --public-demo outputs/public-demo --out outputs/browser-capture
	PYTHONPATH=src $(PYTHON) -m neodojo capture bundle --public-demo outputs/public-demo --viser-runtime outputs/viser-runtime --g1-render outputs/g1-render --browser-capture outputs/browser-capture --out outputs/capture

real-gpu-prep:
	@test -n "$(LOCAL_VIDEO)" || (echo "LOCAL_VIDEO=path/to/local-source.mp4 is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion prepare $(REAL_PREP_SOURCE_ARGS) --start "$(REAL_START)" --end "$(REAL_END)" --local-video "$(LOCAL_VIDEO)" --out "$(REAL_PREP_OUT)"
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion materialize-source --prep "$(REAL_PREP_OUT)/real-conversion-prep.json" --local-video "$(LOCAL_VIDEO)" $(REAL_MATERIALIZE_FLAGS) --out "$(REAL_SOURCE_OUT)"
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion prepare-gpu-run --source-materialization "$(REAL_SOURCE_OUT)/source-materialization.json" --out "$(REAL_GPU_RUN_OUT)"

.real-gpu-prep-smoke:
	rm -rf outputs/real-gpu-prep-smoke
	mkdir -p outputs/real-gpu-prep-smoke
	printf 'fixture source video bytes' > outputs/real-gpu-prep-smoke/source.mp4
	$(MAKE) real-gpu-prep LOCAL_VIDEO=outputs/real-gpu-prep-smoke/source.mp4 REAL_PREP_OUT=outputs/real-gpu-prep-smoke/prep REAL_SOURCE_OUT=outputs/real-gpu-prep-smoke/source-materialized REAL_GPU_RUN_OUT=outputs/real-gpu-prep-smoke/gpu-run
	test -f outputs/real-gpu-prep-smoke/prep/real-conversion-prep.json
	test -f outputs/real-gpu-prep-smoke/source-materialized/source-materialization.json
	test -f outputs/real-gpu-prep-smoke/gpu-run/manifest.json
	test -f outputs/real-gpu-prep-smoke/gpu-run/export_neodojo_gvhmr.py
	test -f outputs/real-gpu-prep-smoke/gpu-run/run_gvhmr_neodojo.sh

gvhmr-inspect:
	@test -n "$(GVHMR_RESULT)" || (echo "GVHMR_RESULT=path/to/hmr4d_results.pt is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion inspect-gvhmr-result --source "$(GVHMR_RESULT)" --out "$(GVHMR_INSPECT_OUT)"

demo-real:
	@test -n "$(SOURCE_MATERIALIZATION)" || (echo "SOURCE_MATERIALIZATION=path/to/source-materialization.json is required" && exit 2)
	@test -n "$(GVHMR_JSON)" || (echo "GVHMR_JSON=path/to/gvhmr-smplx-joints.json is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion import-demo $(REAL_DEMO_ARGS)

mujoco-backend-compare:
	@test -n "$(MODEL_DESCRIPTOR)" || (echo "MODEL_DESCRIPTOR=path/to/g1-model-manifest.json is required" && exit 2)
	@test -n "$(G1_TRACK)" || (echo "G1_TRACK=path/to/g1-track-manifest.json is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo render mujoco-g1-backends --model-descriptor "$(MODEL_DESCRIPTOR)" --g1-track "$(G1_TRACK)" --backends $(MUJOCO_COMPARE_BACKENDS) --width "$(MUJOCO_COMPARE_WIDTH)" --height "$(MUJOCO_COMPARE_HEIGHT)" --out "$(MUJOCO_COMPARE_OUT)"

real-artifact-intake:
	@test -f "$(REAL_ARTIFACT_SOURCE_MATERIALIZATION)" || (echo "REAL_ARTIFACT_SOURCE_MATERIALIZATION=path/to/source-materialization.json is required" && exit 2)
	@test -f "$(REAL_ARTIFACT_GVHMR_JSON)" || (echo "REAL_ARTIFACT_GVHMR_JSON=path/to/gvhmr-smplx-joints.json is required" && exit 2)
	$(MAKE) demo-real SOURCE_MATERIALIZATION="$(REAL_ARTIFACT_SOURCE_MATERIALIZATION)" GVHMR_JSON="$(REAL_ARTIFACT_GVHMR_JSON)" REAL_DEMO_OUT="$(REAL_ARTIFACT_OUT)"

.real-artifact-intake-smoke:
	rm -rf "$(REAL_ARTIFACT_SMOKE_INPUT_OUT)" "$(REAL_ARTIFACT_SMOKE_OUT)"
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion write-intake-smoke-input --out "$(REAL_ARTIFACT_SMOKE_INPUT_OUT)"
	$(MAKE) real-artifact-intake REAL_ARTIFACT_SOURCE_MATERIALIZATION="$(REAL_ARTIFACT_SMOKE_INPUT_OUT)/source-materialization.json" REAL_ARTIFACT_GVHMR_JSON="$(REAL_ARTIFACT_SMOKE_INPUT_OUT)/gvhmr-smplx-joints.json" REAL_ARTIFACT_OUT="$(REAL_ARTIFACT_SMOKE_OUT)"
	test -f "$(REAL_ARTIFACT_SMOKE_OUT)/manifest.json"
	test -f "$(REAL_ARTIFACT_SMOKE_OUT)/public-demo/manifest.json"
	test -f "$(REAL_ARTIFACT_SMOKE_OUT)/capture/manifest.json"

real-conversion-audit:
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion audit-completion $(REAL_CONVERSION_AUDIT_ARGS)
	test -f "$(REAL_CONVERSION_AUDIT_OUT)/manifest.json"

real-conversion-audit-strict:
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion audit-completion $(REAL_CONVERSION_AUDIT_ARGS) --require-complete
	test -f "$(REAL_CONVERSION_AUDIT_OUT)/manifest.json"

smoke-public:
	PYTHONPATH=src $(PYTHON) -m neodojo demo smoke --public-demo outputs/public-demo
