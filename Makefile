.PHONY: all verify lint check test build demo-html demo-public demo-public-browser gpu-handoff gvhmr-inspect demo-real smoke-public

PYTHON ?= python3
GPU_HANDOFF_OUT ?= outputs/gvhmr-gpu-handoff
GVHMR_INSPECT_OUT ?= outputs/gvhmr-result-inspection
REAL_DEMO_OUT ?= outputs/real-demo
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

all: verify

verify: lint check test build demo-public

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

gpu-handoff:
	@test -n "$(SOURCE_MATERIALIZATION)" || (echo "SOURCE_MATERIALIZATION=path/to/source-materialization.json is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion package-gpu-handoff --source-materialization "$(SOURCE_MATERIALIZATION)" --out "$(GPU_HANDOFF_OUT)"

gvhmr-inspect:
	@test -n "$(GVHMR_RESULT)" || (echo "GVHMR_RESULT=path/to/hmr4d_results.pt is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion inspect-gvhmr-result --source "$(GVHMR_RESULT)" --out "$(GVHMR_INSPECT_OUT)"

demo-real:
	@test -n "$(SOURCE_MATERIALIZATION)" || (echo "SOURCE_MATERIALIZATION=path/to/source-materialization.json is required" && exit 2)
	@test -n "$(GVHMR_JSON)" || (echo "GVHMR_JSON=path/to/gvhmr-smplx-joints.json is required" && exit 2)
	PYTHONPATH=src $(PYTHON) -m neodojo real-conversion import-demo $(REAL_DEMO_ARGS)

smoke-public:
	PYTHONPATH=src $(PYTHON) -m neodojo demo smoke --public-demo outputs/public-demo
