.PHONY: dev-install clean build publish

dev-install:
	uv sync --extra dev

clean:
	rm -rf dist/ build/ *.egg-info/

build: clean
	uv build

publish: build
	uv publish
