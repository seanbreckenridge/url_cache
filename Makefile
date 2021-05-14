.DEFAULT_GOAL := install

install:
	python3 -m pip install .

install_testing:
	python3 -m pip install '.[testing]'

docs: install
	python3 -m pip install pdoc3
	rm -rf ./docs
	pdoc3 -o ./docs url_cache

test: install_testing
	pytest
	mypy ./src/url_cache/ ./tests/
