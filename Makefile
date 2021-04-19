.PHONY: docs
init:
	pip install -e .[socks]
	pip install -r requirements-dev.txt
test:
	# This runs all of the tests, on both Python 2 and Python 3.
	detox
ci:
	pytest tests --junitxml=report.xml

flake8:
	flake8 --ignore=E501,F401,E128,E402,E731,F821 fipeapi

coverage:
	pytest --cov-config .coveragerc --verbose --cov-report term --cov-report xml --cov=fipeapi tests

publish:
	pip install 'twine>=1.5.0'
	python setup.py sdist bdist_wheel
	twine upload dist/*
	rm -fr build dist .egg fipeapi.egg-info

docs:
	cd docs && make html
	@echo "\033[95m\n\nBuild successful! View the docs homepage at docs/_build/html/index.html.\n\033[0m"