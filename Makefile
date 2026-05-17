.PHONY: all verify lint check test build demo-html demo-public smoke-public

PYTHON ?= python3

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
	rm -rf outputs/motion-contract outputs/smplx-surface outputs/annotations outputs/g1-visual outputs/g1-render outputs/teaching-demo outputs/public-demo
	PYTHONPATH=src $(PYTHON) -m neodojo motion-record create --out outputs/motion-contract
	PYTHONPATH=src $(PYTHON) -m neodojo smplx-surface proxy --motion-record outputs/motion-contract --out outputs/smplx-surface
	PYTHONPATH=src $(PYTHON) -m neodojo annotations detect --motion-record outputs/motion-contract --out outputs/annotations
	PYTHONPATH=src $(PYTHON) -m neodojo robot-model register --robot unitree_g1 --fixture --out outputs/g1-visual
	PYTHONPATH=src $(PYTHON) -m neodojo tracks build --motion-record outputs/motion-contract --robot unitree_g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --out outputs/g1-visual
	PYTHONPATH=src $(PYTHON) -m neodojo render g1 --model-descriptor outputs/g1-visual/robot-models/unitree_g1/manifest.json --g1-track outputs/g1-visual/tracks/g1/manifest.json --allow-fixture-model --out outputs/g1-render
	PYTHONPATH=src $(PYTHON) -m neodojo demo play --motion-record outputs/motion-contract --g1-track outputs/g1-visual/tracks/g1/manifest.json --annotations outputs/annotations/manifest.json --smplx-surface outputs/smplx-surface/surfaces/smplx/manifest.json --out outputs/teaching-demo
	PYTHONPATH=src $(PYTHON) -m neodojo demo export-rerun --playback outputs/teaching-demo/manifest.json --g1-render outputs/g1-render/manifest.json --out outputs/public-demo/neodojo-demo.rrd
	PYTHONPATH=src $(PYTHON) -m neodojo demo smoke --public-demo outputs/public-demo

smoke-public:
	PYTHONPATH=src $(PYTHON) -m neodojo demo smoke --public-demo outputs/public-demo
