.PHONY: list

list:
	@LC_ALL=C $(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | grep -E -v -e '^[^[:alnum:]]' -e '^$@$$'

init:
	poetry install --sync
	pre-commit install

style:
	pre-commit run black -a

lint:
	pre-commit run ruff -a

test:
	python -m pytest -vlx

clean_notebooks:
	pre-commit run nbstripout -a

exec_notebooks:
	python -m nbconvert --to notebook --execute  --ExecutePreprocessor.kernel_name=python3 --stdout examples/* >/dev/null

mypy:
	dmypy run ./coastlines

deps:
	mkdir -p rquirements
	pre-commit run poetry-lock -a
	pre-commit run poetry-export -a
