.PHONY: all verify verify-real lint check test build demo-html demo-public demo-public-browser real-handoff real-gpu-archive real-gpu-run-request real-gpu-colab-notebook real-handoff-smoke gpu-handoff gpu-input-bundle gpu-input-bundle-smoke gpu-input-archive gpu-input-archive-smoke gpu-execution-probe gvhmr-run-request gvhmr-run-request-smoke gvhmr-colab-notebook gvhmr-colab-notebook-smoke gvhmr-inspect demo-real real-artifact-intake real-artifact-intake-smoke real-conversion-audit real-conversion-audit-strict real-demo-pages-promotion-validate smoke-public

PYTHON ?= python3
REAL_SOURCE_ID ?= 03-006
REAL_START ?= 0
REAL_END ?= 12
REAL_PREP_OUT ?= outputs/real-conversion-gate
REAL_SOURCE_OUT ?= outputs/real-conversion-source
REAL_DRY_RUN ?= 1
GPU_HANDOFF_OUT ?= outputs/gvhmr-gpu-handoff
GPU_INPUT_OUT ?= outputs/gvhmr-gpu-input
GPU_INPUT_INCLUDE_MEDIA ?= 0
GPU_INPUT_ARCHIVE_OUT ?= outputs/gvhmr-gpu-input-archive
GPU_INPUT_ARCHIVE_NAME ?= neodojo-gvhmr-gpu-input.tar.gz
GPU_EXECUTION_PROBE_OUT ?= outputs/gvhmr-gpu-execution-probe
GVHMR_RUN_REQUEST_OUT ?= outputs/gvhmr-gpu-run-request
GVHMR_COLAB_NOTEBOOK_OUT ?= outputs/gvhmr-colab-operator
GVHMR_INSPECT_OUT ?= outputs/gvhmr-result-inspection
REAL_DEMO_OUT ?= outputs/real-demo
REAL_ARTIFACT_SOURCE_MATERIALIZATION ?= outputs/real-conversion-source/source-materialization.json
REAL_ARTIFACT_GVHMR_JSON ?= outputs/real-conversion-gate/gvhmr-smplx-joints.json
REAL_ARTIFACT_OUT ?= outputs/real-demo
REAL_ARTIFACT_SMOKE_INPUT_OUT ?= outputs/real-artifact-intake-smoke-input
REAL_ARTIFACT_SMOKE_OUT ?= outputs/real-artifact-intake-smoke
REAL_CONVERSION_AUDIT_OUT ?= outputs/real-conversion-audit
PROMOTION_DOWNLOAD_ROOT ?= outputs/promoted-real-demo-download
PROMOTION_SOURCE_RUN_ID ?=
PROMOTION_ARTIFACT_NAME ?= neodojo-self-hosted-real-demo
PROMOTION_OUT ?= outputs/promoted-real-demo-pages
REAL_DEMO_ARGS = --source-materialization "$(SOURCE_MATERIALIZATION)" --gvhmr-json "$(GVHMR_JSON)" --out "$(REAL_DEMO_OUT)"
ifdef G1_TRACK
REAL_DEMO_ARGS += --g1-track "$(G1_TRACK)"
endif
ifdef MODEL_DESCRIPTOR
REAL_DEMO_ARGS += --model-descriptor "$(MODEL_DESCRIPTOR)"
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
ifeq ($(GPU_INPUT_INCLUDE_MEDIA),0)
GPU_INPUT_MEDIA_FLAGS =
else
GPU_INPUT_MEDIA_FLAGS = --include-media
endif

all: verify

verify: lint check test build demo-public real-handoff-smoke gpu-input-bundle-smoke gpu-execution-probe gvhmr-run-request-smoke gvhmr-colab-notebook-smoke real-artifact-intake-smoke real-conversion-audit

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

real-handoff:
	@test -n "$(LOCAL_VIDEO)" || (echo "LOCAL_VIDEO=path/to/local-source.mp4 is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion prepare $(REAL_PREP_SOURCE_ARGS) --start "$(REAL_START)" --end "$(REAL_END)" --local-video "$(LOCAL_VIDEO)" --out "$(REAL_PREP_OUT)"
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion materialize-source --prep "$(REAL_PREP_OUT)/real-conversion-prep.json" --local-video "$(LOCAL_VIDEO)" $(REAL_MATERIALIZE_FLAGS) --out "$(REAL_SOURCE_OUT)"
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion package-gpu-handoff --source-materialization "$(REAL_SOURCE_OUT)/source-materialization.json" --out "$(GPU_HANDOFF_OUT)"

real-gpu-archive:
	@test -n "$(LOCAL_VIDEO)" || (echo "LOCAL_VIDEO=path/to/local-source.mp4 is required" && exit 2)
	$(MAKE) real-handoff LOCAL_VIDEO="$(LOCAL_VIDEO)" REAL_DRY_RUN=0 REAL_PREP_OUT="$(REAL_PREP_OUT)" REAL_SOURCE_OUT="$(REAL_SOURCE_OUT)" GPU_HANDOFF_OUT="$(GPU_HANDOFF_OUT)"
	$(MAKE) gpu-input-bundle GPU_HANDOFF="$(GPU_HANDOFF_OUT)" GPU_INPUT_OUT="$(GPU_INPUT_OUT)" GPU_INPUT_INCLUDE_MEDIA=1
	$(MAKE) gpu-input-archive GPU_INPUT="$(GPU_INPUT_OUT)" GPU_INPUT_ARCHIVE_OUT="$(GPU_INPUT_ARCHIVE_OUT)" GPU_INPUT_ARCHIVE_NAME="$(GPU_INPUT_ARCHIVE_NAME)"

real-gpu-run-request:
	@test -n "$(LOCAL_VIDEO)" || (echo "LOCAL_VIDEO=path/to/local-source.mp4 is required" && exit 2)
	$(MAKE) real-gpu-archive LOCAL_VIDEO="$(LOCAL_VIDEO)" REAL_PREP_OUT="$(REAL_PREP_OUT)" REAL_SOURCE_OUT="$(REAL_SOURCE_OUT)" GPU_HANDOFF_OUT="$(GPU_HANDOFF_OUT)" GPU_INPUT_OUT="$(GPU_INPUT_OUT)" GPU_INPUT_ARCHIVE_OUT="$(GPU_INPUT_ARCHIVE_OUT)" GPU_INPUT_ARCHIVE_NAME="$(GPU_INPUT_ARCHIVE_NAME)"
	$(MAKE) gvhmr-run-request GPU_INPUT_ARCHIVE="$(GPU_INPUT_ARCHIVE_OUT)" GVHMR_RUN_REQUEST_OUT="$(GVHMR_RUN_REQUEST_OUT)"
	test -f "$(GVHMR_RUN_REQUEST_OUT)/manifest.json"
	test -f "$(GVHMR_RUN_REQUEST_OUT)/README.md"

real-gpu-colab-notebook:
	@test -n "$(LOCAL_VIDEO)" || (echo "LOCAL_VIDEO=path/to/local-source.mp4 is required" && exit 2)
	$(MAKE) real-gpu-run-request LOCAL_VIDEO="$(LOCAL_VIDEO)" REAL_PREP_OUT="$(REAL_PREP_OUT)" REAL_SOURCE_OUT="$(REAL_SOURCE_OUT)" GPU_HANDOFF_OUT="$(GPU_HANDOFF_OUT)" GPU_INPUT_OUT="$(GPU_INPUT_OUT)" GPU_INPUT_ARCHIVE_OUT="$(GPU_INPUT_ARCHIVE_OUT)" GPU_INPUT_ARCHIVE_NAME="$(GPU_INPUT_ARCHIVE_NAME)" GVHMR_RUN_REQUEST_OUT="$(GVHMR_RUN_REQUEST_OUT)"
	$(MAKE) gvhmr-colab-notebook GVHMR_RUN_REQUEST="$(GVHMR_RUN_REQUEST_OUT)" GVHMR_COLAB_NOTEBOOK_OUT="$(GVHMR_COLAB_NOTEBOOK_OUT)"
	test -f "$(GVHMR_COLAB_NOTEBOOK_OUT)/manifest.json"
	test -f "$(GVHMR_COLAB_NOTEBOOK_OUT)/gvhmr-colab-operator.ipynb"

real-handoff-smoke:
	rm -rf outputs/real-handoff-smoke
	mkdir -p outputs/real-handoff-smoke
	printf 'fixture source video bytes' > outputs/real-handoff-smoke/source.mp4
	$(MAKE) real-handoff LOCAL_VIDEO=outputs/real-handoff-smoke/source.mp4 REAL_PREP_OUT=outputs/real-handoff-smoke/prep REAL_SOURCE_OUT=outputs/real-handoff-smoke/source-materialized GPU_HANDOFF_OUT=outputs/real-handoff-smoke/gpu-handoff
	test -f outputs/real-handoff-smoke/prep/real-conversion-prep.json
	test -f outputs/real-handoff-smoke/source-materialized/source-materialization.json
	test -f outputs/real-handoff-smoke/gpu-handoff/manifest.json
	test -f outputs/real-handoff-smoke/gpu-handoff/export_neodojo_gvhmr.py
	test -f outputs/real-handoff-smoke/gpu-handoff/run_gvhmr_neodojo.sh

gpu-handoff:
	@test -n "$(SOURCE_MATERIALIZATION)" || (echo "SOURCE_MATERIALIZATION=path/to/source-materialization.json is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion package-gpu-handoff --source-materialization "$(SOURCE_MATERIALIZATION)" --out "$(GPU_HANDOFF_OUT)"

gpu-input-bundle:
	@test -n "$(GPU_HANDOFF)" || (echo "GPU_HANDOFF=path/to/gpu-handoff is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion package-gpu-input --gpu-handoff "$(GPU_HANDOFF)" $(GPU_INPUT_MEDIA_FLAGS) --out "$(GPU_INPUT_OUT)"

gpu-input-bundle-smoke: real-handoff-smoke
	rm -rf outputs/gvhmr-gpu-input-smoke
	$(MAKE) gpu-input-bundle GPU_HANDOFF=outputs/real-handoff-smoke/gpu-handoff GPU_INPUT_OUT=outputs/gvhmr-gpu-input-smoke
	test -f outputs/gvhmr-gpu-input-smoke/manifest.json
	test -f outputs/gvhmr-gpu-input-smoke/RUN_ON_GPU.md
	test -f outputs/gvhmr-gpu-input-smoke/run_gvhmr_neodojo.sh
	bash -n outputs/gvhmr-gpu-input-smoke/run_gvhmr_neodojo.sh

gpu-input-archive:
	@test -n "$(GPU_INPUT)" || (echo "GPU_INPUT=path/to/gpu-input-bundle is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion archive-gpu-input --gpu-input "$(GPU_INPUT)" --archive-name "$(GPU_INPUT_ARCHIVE_NAME)" --out "$(GPU_INPUT_ARCHIVE_OUT)"

gpu-input-archive-smoke: gpu-input-bundle-smoke
	rm -rf outputs/gvhmr-gpu-input-archive-smoke
	$(MAKE) gpu-input-archive GPU_INPUT=outputs/gvhmr-gpu-input-smoke GPU_INPUT_ARCHIVE_OUT=outputs/gvhmr-gpu-input-archive-smoke
	test -f outputs/gvhmr-gpu-input-archive-smoke/manifest.json
	test -f outputs/gvhmr-gpu-input-archive-smoke/neodojo-gvhmr-gpu-input.tar.gz
	$(PYTHON) -m tarfile -l outputs/gvhmr-gpu-input-archive-smoke/neodojo-gvhmr-gpu-input.tar.gz

gpu-execution-probe:
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion probe-gpu-execution --out "$(GPU_EXECUTION_PROBE_OUT)"
	test -f "$(GPU_EXECUTION_PROBE_OUT)/manifest.json"

gvhmr-run-request:
	@test -n "$(GPU_INPUT_ARCHIVE)" || (echo "GPU_INPUT_ARCHIVE=path/to/gpu-input-archive-manifest-or-dir is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion write-gpu-run-request --gpu-input-archive "$(GPU_INPUT_ARCHIVE)" --out "$(GVHMR_RUN_REQUEST_OUT)"

gvhmr-run-request-smoke: gpu-input-archive-smoke
	rm -rf outputs/gvhmr-gpu-run-request-smoke
	$(MAKE) gvhmr-run-request GPU_INPUT_ARCHIVE=outputs/gvhmr-gpu-input-archive-smoke GVHMR_RUN_REQUEST_OUT=outputs/gvhmr-gpu-run-request-smoke
	test -f outputs/gvhmr-gpu-run-request-smoke/manifest.json
	test -f outputs/gvhmr-gpu-run-request-smoke/README.md

gvhmr-colab-notebook:
	@test -n "$(GVHMR_RUN_REQUEST)" || (echo "GVHMR_RUN_REQUEST=path/to/gpu-run-request-manifest-or-dir is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion write-colab-notebook --gpu-run-request "$(GVHMR_RUN_REQUEST)" --out "$(GVHMR_COLAB_NOTEBOOK_OUT)"

gvhmr-colab-notebook-smoke: gvhmr-run-request-smoke
	rm -rf outputs/gvhmr-colab-operator-smoke
	$(MAKE) gvhmr-colab-notebook GVHMR_RUN_REQUEST=outputs/gvhmr-gpu-run-request-smoke GVHMR_COLAB_NOTEBOOK_OUT=outputs/gvhmr-colab-operator-smoke
	test -f outputs/gvhmr-colab-operator-smoke/manifest.json
	test -f outputs/gvhmr-colab-operator-smoke/gvhmr-colab-operator.ipynb

gvhmr-inspect:
	@test -n "$(GVHMR_RESULT)" || (echo "GVHMR_RESULT=path/to/hmr4d_results.pt is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion inspect-gvhmr-result --source "$(GVHMR_RESULT)" --out "$(GVHMR_INSPECT_OUT)"

demo-real:
	@test -n "$(SOURCE_MATERIALIZATION)" || (echo "SOURCE_MATERIALIZATION=path/to/source-materialization.json is required" && exit 2)
	@test -n "$(GVHMR_JSON)" || (echo "GVHMR_JSON=path/to/gvhmr-smplx-joints.json is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion import-demo $(REAL_DEMO_ARGS)

real-artifact-intake:
	@test -f "$(REAL_ARTIFACT_SOURCE_MATERIALIZATION)" || (echo "REAL_ARTIFACT_SOURCE_MATERIALIZATION=path/to/source-materialization.json is required" && exit 2)
	@test -f "$(REAL_ARTIFACT_GVHMR_JSON)" || (echo "REAL_ARTIFACT_GVHMR_JSON=path/to/gvhmr-smplx-joints.json is required" && exit 2)
	$(MAKE) demo-real SOURCE_MATERIALIZATION="$(REAL_ARTIFACT_SOURCE_MATERIALIZATION)" GVHMR_JSON="$(REAL_ARTIFACT_GVHMR_JSON)" REAL_DEMO_OUT="$(REAL_ARTIFACT_OUT)"

real-artifact-intake-smoke:
	rm -rf "$(REAL_ARTIFACT_SMOKE_INPUT_OUT)" "$(REAL_ARTIFACT_SMOKE_OUT)"
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion write-intake-smoke-input --out "$(REAL_ARTIFACT_SMOKE_INPUT_OUT)"
	$(MAKE) real-artifact-intake REAL_ARTIFACT_SOURCE_MATERIALIZATION="$(REAL_ARTIFACT_SMOKE_INPUT_OUT)/source-materialization.json" REAL_ARTIFACT_GVHMR_JSON="$(REAL_ARTIFACT_SMOKE_INPUT_OUT)/gvhmr-smplx-joints.json" REAL_ARTIFACT_OUT="$(REAL_ARTIFACT_SMOKE_OUT)"
	test -f "$(REAL_ARTIFACT_SMOKE_OUT)/manifest.json"
	test -f "$(REAL_ARTIFACT_SMOKE_OUT)/public-demo/manifest.json"
	test -f "$(REAL_ARTIFACT_SMOKE_OUT)/capture/manifest.json"

real-conversion-audit:
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion audit-completion --source-materialization "$(REAL_ARTIFACT_SOURCE_MATERIALIZATION)" --gvhmr-json "$(REAL_ARTIFACT_GVHMR_JSON)" --real-demo "$(REAL_ARTIFACT_OUT)" --out "$(REAL_CONVERSION_AUDIT_OUT)"
	test -f "$(REAL_CONVERSION_AUDIT_OUT)/manifest.json"

real-conversion-audit-strict:
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion audit-completion --source-materialization "$(REAL_ARTIFACT_SOURCE_MATERIALIZATION)" --gvhmr-json "$(REAL_ARTIFACT_GVHMR_JSON)" --real-demo "$(REAL_ARTIFACT_OUT)" --out "$(REAL_CONVERSION_AUDIT_OUT)" --require-complete
	test -f "$(REAL_CONVERSION_AUDIT_OUT)/manifest.json"

real-demo-pages-promotion-validate:
	@test -n "$(PROMOTION_SOURCE_RUN_ID)" || (echo "PROMOTION_SOURCE_RUN_ID=<github-actions-run-id> is required" && exit 2)
	@test -d "$(PROMOTION_DOWNLOAD_ROOT)" || (echo "PROMOTION_DOWNLOAD_ROOT=path/to/downloaded-real-demo-artifact is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion validate-pages-promotion --download-root "$(PROMOTION_DOWNLOAD_ROOT)" --source-run-id "$(PROMOTION_SOURCE_RUN_ID)" --artifact-name "$(PROMOTION_ARTIFACT_NAME)" --out "$(PROMOTION_OUT)"

smoke-public:
	PYTHONPATH=src $(PYTHON) -m neodojo demo smoke --public-demo outputs/public-demo
