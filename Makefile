.PHONY: all verify verify-real lint check test build demo-html demo-public demo-public-browser readme-gif bilibili-download routine-split routine-prepare-gpu routine-assemble routine-smoke real-gpu-prep gvhmr-inspect demo-real ci-real-demo mujoco-g1-render roboharness-g1-report mujoco-backend-compare mujoco-backend-benchmark real-artifact-intake real-conversion-audit real-conversion-audit-strict smoke-public

PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
ROUTINE ?= baduanjin
BILIBILI_DOWNLOAD_OUT ?= outputs/bilibili-download
BILIBILI_MEDIA_DIR ?=
BILIBILI_QUALITY ?= 480p
BILIBILI_DRY_RUN ?= 1
BILIBILI_COOKIES ?=
BILIBILI_COOKIES_FROM_BROWSER ?=
ROUTINE_SOURCE_VIDEO ?=
ROUTINE_SOURCE_OUT ?= outputs/routines/$(ROUTINE)/source
ROUTINE_GPU_OUT ?= outputs/routines/$(ROUTINE)/gvhmr-runs
ROUTINE_HTML_OUT ?= outputs/routines/$(ROUTINE)/html
ROUTINE_GVHMR_JSON_ROOT ?= outputs/routines/$(ROUTINE)/gvhmr-runs
ROUTINE_GMR_JSON_ROOT ?= outputs/routines/$(ROUTINE)/gmr-json
ROUTINE_MODEL_DESCRIPTOR ?=
ROUTINE_FRAME_RATE ?= 1
ROUTINE_DRY_RUN ?= 1
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
MUJOCO_RENDER_GL ?= glfw
MUJOCO_RENDER_WIDTH ?= 1280
MUJOCO_RENDER_HEIGHT ?= 960
MUJOCO_RENDER_OUT ?= outputs/g1-mujoco-render
ROBOHARNESS_REPORT_OUT ?= outputs/g1-roboharness-report
MUJOCO_COMPARE_BACKENDS ?= egl glfw osmesa
MUJOCO_COMPARE_WIDTH ?= 1280
MUJOCO_COMPARE_HEIGHT ?= 960
MUJOCO_COMPARE_OUT ?= outputs/g1-mujoco-backend-comparison
MUJOCO_BENCHMARK_BACKENDS ?= egl glfw osmesa
MUJOCO_BENCHMARK_WIDTH ?= 1280
MUJOCO_BENCHMARK_HEIGHT ?= 960
MUJOCO_BENCHMARK_RUNS ?= 2
MUJOCO_BENCHMARK_WARMUP_RUNS ?= 0
MUJOCO_BENCHMARK_OUT ?= outputs/g1-mujoco-backend-benchmark
REAL_ARTIFACT_SMOKE_INPUT_OUT ?= outputs/real-artifact-intake-smoke-input
REAL_ARTIFACT_SMOKE_OUT ?= outputs/real-artifact-intake-smoke
SAMPLE_BADUANJIN_ROOT ?= samples/baduanjin-03-006-two-hands-80-92
SAMPLE_BADUANJIN_SOURCE_MATERIALIZATION ?= $(SAMPLE_BADUANJIN_ROOT)/source/source-materialization.json
SAMPLE_BADUANJIN_GVHMR_JSON ?= $(SAMPLE_BADUANJIN_ROOT)/gvhmr/gvhmr-smplx-joints.json
SAMPLE_BADUANJIN_GMR_G1_JSON ?= $(SAMPLE_BADUANJIN_ROOT)/gmr/gmr-unitree-g1.json
CI_REAL_DEMO_INPUT_OUT ?= outputs/ci-real-demo-input
CI_REAL_DEMO_OUT ?= outputs/real-demo
CI_REAL_MOTION_OUT ?= outputs/ci-real-motion-contract
CI_REAL_MODEL_OUT ?= outputs/ci-real-g1-model
CI_REAL_G1_TRACK_OUT ?= outputs/ci-real-g1-track
CI_REAL_G1_RENDER_OUT ?= outputs/ci-real-g1-render
CI_REAL_SOURCE_MATERIALIZATION ?=
CI_REAL_GVHMR_JSON ?=
CI_REAL_GMR_G1_JSON ?=
CI_REAL_G1_TRACK ?=
CI_REAL_MODEL_DESCRIPTOR ?=
CI_REAL_G1_RENDER ?=
CI_REAL_RENDER_MUJOCO ?=
CI_REAL_USE_RERUN_SDK ?=
CI_REAL_VERIFY_STRICT ?= 1
README_GIF_PUBLIC_DEMO ?= outputs/real-demo/public-demo
README_GIF_OUT ?= docs/assets/neodojo-sample.gif
README_GIF_FRAMES ?= 24
README_GIF_SCALE_WIDTH ?= 960
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
CI_REAL_DEMO_ARGS = SOURCE_MATERIALIZATION="$(CI_REAL_SOURCE_MATERIALIZATION)" GVHMR_JSON="$(CI_REAL_GVHMR_JSON)" REAL_DEMO_OUT="$(CI_REAL_DEMO_OUT)"
ifdef CI_REAL_G1_TRACK
CI_REAL_DEMO_ARGS += G1_TRACK="$(CI_REAL_G1_TRACK)"
endif
ifdef CI_REAL_MODEL_DESCRIPTOR
CI_REAL_DEMO_ARGS += MODEL_DESCRIPTOR="$(CI_REAL_MODEL_DESCRIPTOR)"
endif
ifdef CI_REAL_G1_RENDER
CI_REAL_DEMO_ARGS += G1_RENDER="$(CI_REAL_G1_RENDER)"
endif
ifdef CI_REAL_RENDER_MUJOCO
CI_REAL_DEMO_ARGS += RENDER_MUJOCO="$(CI_REAL_RENDER_MUJOCO)"
endif
ifdef CI_REAL_USE_RERUN_SDK
CI_REAL_DEMO_ARGS += USE_RERUN_SDK="$(CI_REAL_USE_RERUN_SDK)"
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
BILIBILI_DOWNLOAD_ARGS = --quality "$(BILIBILI_QUALITY)" --out "$(BILIBILI_DOWNLOAD_OUT)"
ifdef BILIBILI_MEDIA_DIR
BILIBILI_DOWNLOAD_ARGS += --media-dir "$(BILIBILI_MEDIA_DIR)"
endif
ifdef BILIBILI_COOKIES
BILIBILI_DOWNLOAD_ARGS += --cookies "$(BILIBILI_COOKIES)"
endif
ifdef BILIBILI_COOKIES_FROM_BROWSER
BILIBILI_DOWNLOAD_ARGS += --cookies-from-browser "$(BILIBILI_COOKIES_FROM_BROWSER)"
endif
ifeq ($(BILIBILI_DRY_RUN),1)
BILIBILI_DOWNLOAD_ARGS += --dry-run
endif
ROUTINE_SPLIT_ARGS = --routine "$(ROUTINE)" --frame-rate "$(ROUTINE_FRAME_RATE)" --out "$(ROUTINE_SOURCE_OUT)"
ifdef ROUTINE_SOURCE_VIDEO
ROUTINE_SPLIT_ARGS += --source-video "$(ROUTINE_SOURCE_VIDEO)"
endif
ifeq ($(ROUTINE_DRY_RUN),1)
ROUTINE_SPLIT_ARGS += --dry-run
endif
ROUTINE_ASSEMBLE_ARGS = --routine "$(ROUTINE)" --source-materializations "$(ROUTINE_SOURCE_OUT)" --gvhmr-json-root "$(ROUTINE_GVHMR_JSON_ROOT)" --gmr-json-root "$(ROUTINE_GMR_JSON_ROOT)" --out "$(ROUTINE_HTML_OUT)"
ifdef ROUTINE_MODEL_DESCRIPTOR
ROUTINE_ASSEMBLE_ARGS += --model-descriptor "$(ROUTINE_MODEL_DESCRIPTOR)"
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

readme-gif: ci-real-demo
	PYTHONPATH=src $(PYTHON) -m neodojo demo render-gif --public-demo "$(README_GIF_PUBLIC_DEMO)" --out "$(README_GIF_OUT)" --frames "$(README_GIF_FRAMES)" --scale-width "$(README_GIF_SCALE_WIDTH)"

bilibili-download:
	PYTHONPATH=src $(PYTHON) -m neodojo bilibili download $(BILIBILI_DOWNLOAD_ARGS)

routine-split:
	PYTHONPATH=src $(PYTHON) -m neodojo routine split $(ROUTINE_SPLIT_ARGS)

routine-prepare-gpu:
	PYTHONPATH=src $(PYTHON) -m neodojo routine prepare-gpu-runs --routine "$(ROUTINE)" --clips "$(ROUTINE_SOURCE_OUT)" --out "$(ROUTINE_GPU_OUT)"

routine-assemble:
	PYTHONPATH=src $(PYTHON) -m neodojo routine assemble $(ROUTINE_ASSEMBLE_ARGS)

routine-smoke:
	PYTHONPATH=src $(PYTHON) -m neodojo routine smoke --routine-html "$(ROUTINE_HTML_OUT)"

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

ci-real-demo:
	rm -rf "$(CI_REAL_DEMO_OUT)" "$(CI_REAL_MOTION_OUT)" "$(CI_REAL_MODEL_OUT)" "$(CI_REAL_G1_TRACK_OUT)" "$(CI_REAL_G1_RENDER_OUT)"
	@if [ -n "$(CI_REAL_GMR_G1_JSON)" ]; then \
		test -f "$(CI_REAL_SOURCE_MATERIALIZATION)" || (echo "CI_REAL_SOURCE_MATERIALIZATION=path/to/source-materialization.json is required" && exit 2); \
		test -f "$(CI_REAL_GVHMR_JSON)" || (echo "CI_REAL_GVHMR_JSON=path/to/gvhmr-smplx-joints.json is required" && exit 2); \
		test -f "$(CI_REAL_GMR_G1_JSON)" || (echo "CI_REAL_GMR_G1_JSON=path/to/gmr-unitree-g1.json is required" && exit 2); \
		PYTHONPATH=src $(PYTHON) -m neodojo motion-record create --from-gvhmr-json "$(CI_REAL_GVHMR_JSON)" --out "$(CI_REAL_MOTION_OUT)"; \
		PYTHONPATH=src $(PYTHON) -m neodojo robot-model register-roboharness-g1 --out "$(CI_REAL_MODEL_OUT)"; \
		PYTHONPATH=src $(PYTHON) -m neodojo tracks import-gmr-json --source "$(CI_REAL_GMR_G1_JSON)" --motion-record "$(CI_REAL_MOTION_OUT)" --model-descriptor "$(CI_REAL_MODEL_OUT)/robot-models/unitree_g1/manifest.json" --out "$(CI_REAL_G1_TRACK_OUT)"; \
		$(MAKE) mujoco-g1-render MODEL_DESCRIPTOR="$(CI_REAL_MODEL_OUT)/robot-models/unitree_g1/manifest.json" G1_TRACK="$(CI_REAL_G1_TRACK_OUT)/tracks/g1/manifest.json" MUJOCO_RENDER_OUT="$(CI_REAL_G1_RENDER_OUT)"; \
		$(MAKE) demo-real SOURCE_MATERIALIZATION="$(CI_REAL_SOURCE_MATERIALIZATION)" GVHMR_JSON="$(CI_REAL_GVHMR_JSON)" G1_TRACK="$(CI_REAL_G1_TRACK_OUT)/tracks/g1/manifest.json" MODEL_DESCRIPTOR="$(CI_REAL_MODEL_OUT)/robot-models/unitree_g1/manifest.json" G1_RENDER="$(CI_REAL_G1_RENDER_OUT)/manifest.json" REAL_DEMO_OUT="$(CI_REAL_DEMO_OUT)"; \
	elif [ -z "$(CI_REAL_SOURCE_MATERIALIZATION)" ] && [ -z "$(CI_REAL_GVHMR_JSON)" ] && [ -f "$(SAMPLE_BADUANJIN_SOURCE_MATERIALIZATION)" ] && [ -f "$(SAMPLE_BADUANJIN_GVHMR_JSON)" ] && [ -f "$(SAMPLE_BADUANJIN_GMR_G1_JSON)" ]; then \
		PYTHONPATH=src $(PYTHON) -m neodojo motion-record create --from-gvhmr-json "$(SAMPLE_BADUANJIN_GVHMR_JSON)" --out "$(CI_REAL_MOTION_OUT)"; \
		PYTHONPATH=src $(PYTHON) -m neodojo robot-model register-roboharness-g1 --out "$(CI_REAL_MODEL_OUT)"; \
		PYTHONPATH=src $(PYTHON) -m neodojo tracks import-gmr-json --source "$(SAMPLE_BADUANJIN_GMR_G1_JSON)" --motion-record "$(CI_REAL_MOTION_OUT)" --model-descriptor "$(CI_REAL_MODEL_OUT)/robot-models/unitree_g1/manifest.json" --out "$(CI_REAL_G1_TRACK_OUT)"; \
		$(MAKE) mujoco-g1-render MODEL_DESCRIPTOR="$(CI_REAL_MODEL_OUT)/robot-models/unitree_g1/manifest.json" G1_TRACK="$(CI_REAL_G1_TRACK_OUT)/tracks/g1/manifest.json" MUJOCO_RENDER_OUT="$(CI_REAL_G1_RENDER_OUT)"; \
		$(MAKE) demo-real SOURCE_MATERIALIZATION="$(SAMPLE_BADUANJIN_SOURCE_MATERIALIZATION)" GVHMR_JSON="$(SAMPLE_BADUANJIN_GVHMR_JSON)" G1_TRACK="$(CI_REAL_G1_TRACK_OUT)/tracks/g1/manifest.json" MODEL_DESCRIPTOR="$(CI_REAL_MODEL_OUT)/robot-models/unitree_g1/manifest.json" G1_RENDER="$(CI_REAL_G1_RENDER_OUT)/manifest.json" REAL_DEMO_OUT="$(CI_REAL_DEMO_OUT)"; \
	elif [ -n "$(CI_REAL_SOURCE_MATERIALIZATION)" ] || [ -n "$(CI_REAL_GVHMR_JSON)" ]; then \
		test -f "$(CI_REAL_SOURCE_MATERIALIZATION)" || (echo "CI_REAL_SOURCE_MATERIALIZATION=path/to/source-materialization.json is required" && exit 2); \
		test -f "$(CI_REAL_GVHMR_JSON)" || (echo "CI_REAL_GVHMR_JSON=path/to/gvhmr-smplx-joints.json is required" && exit 2); \
		$(MAKE) demo-real $(CI_REAL_DEMO_ARGS); \
	else \
		rm -rf "$(CI_REAL_DEMO_INPUT_OUT)"; \
		PYTHONPATH=src $(PYTHON) -m neodojo real-conversion write-intake-smoke-input --out "$(CI_REAL_DEMO_INPUT_OUT)"; \
		$(MAKE) demo-real SOURCE_MATERIALIZATION="$(CI_REAL_DEMO_INPUT_OUT)/source-materialization.json" GVHMR_JSON="$(CI_REAL_DEMO_INPUT_OUT)/gvhmr-smplx-joints.json" REAL_DEMO_OUT="$(CI_REAL_DEMO_OUT)"; \
	fi
	test -f "$(CI_REAL_DEMO_OUT)/public-demo/index.html"
	PYTHONPATH=src $(PYTHON) -m neodojo demo smoke --public-demo "$(CI_REAL_DEMO_OUT)/public-demo"
	@if [ "$(CI_REAL_VERIFY_STRICT)" = "1" ]; then \
		if [ -n "$(CI_REAL_SOURCE_MATERIALIZATION)" ] || [ -n "$(CI_REAL_GVHMR_JSON)" ]; then \
			test -f "$(CI_REAL_SOURCE_MATERIALIZATION)" || (echo "CI_REAL_VERIFY_STRICT=1 requires CI_REAL_SOURCE_MATERIALIZATION=path/to/source-materialization.json" && exit 2); \
			test -f "$(CI_REAL_GVHMR_JSON)" || (echo "CI_REAL_VERIFY_STRICT=1 requires CI_REAL_GVHMR_JSON=path/to/gvhmr-smplx-joints.json" && exit 2); \
			$(MAKE) verify-real REAL_ARTIFACT_SOURCE_MATERIALIZATION="$(CI_REAL_SOURCE_MATERIALIZATION)" REAL_ARTIFACT_GVHMR_JSON="$(CI_REAL_GVHMR_JSON)" REAL_ARTIFACT_OUT="$(CI_REAL_DEMO_OUT)"; \
		else \
			$(MAKE) verify-real REAL_ARTIFACT_SOURCE_MATERIALIZATION="$(SAMPLE_BADUANJIN_SOURCE_MATERIALIZATION)" REAL_ARTIFACT_GVHMR_JSON="$(SAMPLE_BADUANJIN_GVHMR_JSON)" REAL_ARTIFACT_OUT="$(CI_REAL_DEMO_OUT)"; \
		fi; \
	fi

mujoco-g1-render:
	@test -n "$(MODEL_DESCRIPTOR)" || (echo "MODEL_DESCRIPTOR=path/to/g1-model-manifest.json is required" && exit 2)
	@test -n "$(G1_TRACK)" || (echo "G1_TRACK=path/to/g1-track-manifest.json is required" && exit 2)
	@if [ "$(MUJOCO_RENDER_GL)" = "glfw" ]; then \
		command -v xvfb-run >/dev/null || (echo "xvfb-run is required for MUJOCO_RENDER_GL=glfw; install xvfb or choose MUJOCO_RENDER_GL=egl/osmesa" && exit 2); \
		xvfb-run -a env MUJOCO_GL="$(MUJOCO_RENDER_GL)" PYTHONPATH=src $(PYTHON) -m neodojo render mujoco-g1 --model-descriptor "$(MODEL_DESCRIPTOR)" --g1-track "$(G1_TRACK)" --width "$(MUJOCO_RENDER_WIDTH)" --height "$(MUJOCO_RENDER_HEIGHT)" --out "$(MUJOCO_RENDER_OUT)"; \
	else \
		env MUJOCO_GL="$(MUJOCO_RENDER_GL)" PYTHONPATH=src $(PYTHON) -m neodojo render mujoco-g1 --model-descriptor "$(MODEL_DESCRIPTOR)" --g1-track "$(G1_TRACK)" --width "$(MUJOCO_RENDER_WIDTH)" --height "$(MUJOCO_RENDER_HEIGHT)" --out "$(MUJOCO_RENDER_OUT)"; \
	fi

roboharness-g1-report:
	@test -n "$(MODEL_DESCRIPTOR)" || (echo "MODEL_DESCRIPTOR=path/to/g1-model-manifest.json is required" && exit 2)
	@test -n "$(G1_TRACK)" || (echo "G1_TRACK=path/to/g1-track-manifest.json is required" && exit 2)
	@if [ "$(MUJOCO_RENDER_GL)" = "glfw" ]; then \
		command -v xvfb-run >/dev/null || (echo "xvfb-run is required for MUJOCO_RENDER_GL=glfw; install xvfb or choose MUJOCO_RENDER_GL=egl/osmesa" && exit 2); \
		xvfb-run -a env MUJOCO_GL="$(MUJOCO_RENDER_GL)" PYTHONPATH=src $(PYTHON) -m neodojo render roboharness-g1 --model-descriptor "$(MODEL_DESCRIPTOR)" --g1-track "$(G1_TRACK)" --width "$(MUJOCO_RENDER_WIDTH)" --height "$(MUJOCO_RENDER_HEIGHT)" --out "$(ROBOHARNESS_REPORT_OUT)"; \
	else \
		env MUJOCO_GL="$(MUJOCO_RENDER_GL)" PYTHONPATH=src $(PYTHON) -m neodojo render roboharness-g1 --model-descriptor "$(MODEL_DESCRIPTOR)" --g1-track "$(G1_TRACK)" --width "$(MUJOCO_RENDER_WIDTH)" --height "$(MUJOCO_RENDER_HEIGHT)" --out "$(ROBOHARNESS_REPORT_OUT)"; \
	fi

mujoco-backend-compare:
	@test -n "$(MODEL_DESCRIPTOR)" || (echo "MODEL_DESCRIPTOR=path/to/g1-model-manifest.json is required" && exit 2)
	@test -n "$(G1_TRACK)" || (echo "G1_TRACK=path/to/g1-track-manifest.json is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo render mujoco-g1-backends --model-descriptor "$(MODEL_DESCRIPTOR)" --g1-track "$(G1_TRACK)" --backends $(MUJOCO_COMPARE_BACKENDS) --width "$(MUJOCO_COMPARE_WIDTH)" --height "$(MUJOCO_COMPARE_HEIGHT)" --out "$(MUJOCO_COMPARE_OUT)"

mujoco-backend-benchmark:
	@test -n "$(MODEL_DESCRIPTOR)" || (echo "MODEL_DESCRIPTOR=path/to/g1-model-manifest.json is required" && exit 2)
	@test -n "$(G1_TRACK)" || (echo "G1_TRACK=path/to/g1-track-manifest.json is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo render mujoco-g1-benchmark --model-descriptor "$(MODEL_DESCRIPTOR)" --g1-track "$(G1_TRACK)" --backends $(MUJOCO_BENCHMARK_BACKENDS) --width "$(MUJOCO_BENCHMARK_WIDTH)" --height "$(MUJOCO_BENCHMARK_HEIGHT)" --runs "$(MUJOCO_BENCHMARK_RUNS)" --warmup-runs "$(MUJOCO_BENCHMARK_WARMUP_RUNS)" --out "$(MUJOCO_BENCHMARK_OUT)"

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
