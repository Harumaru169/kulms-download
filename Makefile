.PHONY: dev-install clean build publish

dev-install:
	pip install -e ".[dev]"

clean:
	rm -rf dist/ build/ *.egg-info/

build: clean
	python -m build

publish: build
	twine upload dist/*
