.PHONY: clean build publish

clean:
	rm -rf dist/ build/ *.egg-info/

build: clean
	python -m build

publish: build
	twine upload dist/*
