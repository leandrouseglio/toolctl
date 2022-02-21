##
## DO NOT MODIFY THIS FILE!
##
## Tu upgrade the build system run in this directory:
##      mcafee-cookiecutter python
## Then when asked about the project_name use: metamorphctl
##

include $(shell git rev-parse --show-toplevel)/Makefile.common
include Makefile.specifics

PROJECT_NAME := metamorphctl
PYTHON_FILES := $(shell find . -name '*.py' -type f)

ARTIFACTS_DIST_PATH := $(ARTIFACTS_OUTPUT_PATH)/dist

OUT_UNIT_TEST_FILE_XML := $(ARTIFACTS_UNIT_TEST_PATH)/$(PROJECT_NAME).xml
OUT_UNIT_TEST_FILE_HTML := $(ARTIFACTS_UNIT_TEST_PATH)/$(PROJECT_NAME).html
OUT_COVERAGE_FILE_XML := $(ARTIFACTS_COVERAGE_PATH)/$(PROJECT_NAME).xml
OUT_COVERAGE_FILE_HTML := $(ARTIFACTS_COVERAGE_PATH)/$(PROJECT_NAME).html
OUT_COVERAGE_FILE_SETTINGS := $(ARTIFACTS_COVERAGE_PATH)/.coveragerc_$(PROJECT_NAME)
OUT_COVERAGE_FILE_DATA := $(ARTIFACTS_COVERAGE_PATH)/.coverage_$(PROJECT_NAME)
OUT_PROSPECTOR_FILE_SETTINGS := $(ARTIFACTS_COVERAGE_PATH)/.prospector_$(PROJECT_NAME).yaml
OUT_BANDIT_FILE_SETTINGS := $(ARTIFACTS_COVERAGE_PATH)/.bandit_$(PROJECT_NAME)
OUT_SECURITY_FILE_HTML := $(ARTIFACTS_SECURITY_PATH)/index_$(PROJECT_NAME).html
OUT_SAFETY_FILE_LOG := $(ARTIFACTS_SECURITY_PATH)/safety_$(PROJECT_NAME).log
OUT_DEPENDENCY_CHECK_FILE_HTML := $(ARTIFACTS_SECURITY_PATH)/dependency_check_$(PROJECT_NAME).html
OUT_DEPENDENCY_CHECK_FILE_LOG := $(ARTIFACTS_SECURITY_PATH)/dependency_check_$(PROJECT_NAME).log

DEPCHECK_VERSION := 5.2.2
DEPCHECK_DIR := $(HOME)/.depcheck

$(OUT_UNIT_TEST_FILE_XML): $(PYTHON_FILES) .coveragerc Pipfile Makefile
	@mkdir -p $(ARTIFACTS_UNIT_TEST_PATH)
	@mkdir -p $(ARTIFACTS_COVERAGE_PATH)
	@cp .coveragerc $(OUT_COVERAGE_FILE_SETTINGS)
	@cp .prospector.yaml $(OUT_PROSPECTOR_FILE_SETTINGS)
	@cp .bandit $(OUT_BANDIT_FILE_SETTINGS)
	@unset PYTHONPATH; \
	  pipenv run pytest $(UNITTEST_ARGS) \
		--verbose \
		--numprocesses=auto \
		--junit-xml=$(OUT_UNIT_TEST_FILE_XML) \
		--html=$(OUT_UNIT_TEST_FILE_HTML) \
		--self-contained-html \
		--cov \
		--cov-branch \
		--cov-fail-under=$(COVERAGE_MINIMUM) \
		--cov-report=html:$(OUT_COVERAGE_FILE_HTML) \
		--cov-report=xml:$(OUT_COVERAGE_FILE_XML) \
		--cov-report=term-missing \
		--color=yes \
		. || (rm -rf $(OUT_UNIT_TEST_FILE_XML); exit 1)
	@cp .coverage $(OUT_COVERAGE_FILE_DATA)

test-unit: $(OUT_UNIT_TEST_FILE_XML)

$(OUT_SECURITY_FILE_HTML): $(PYTHON_FILES) .bandit Makefile
	@mkdir -p $(ARTIFACTS_SECURITY_PATH)
	@pipenv run  -- bandit -v -r . -f html -o $(OUT_SECURITY_FILE_HTML) \
		|| (printf "$$(tput setaf 1)\n\nSecurity vulns found see: $(OUT_SECURITY_FILE_HTML)\n\n$$(tput sgr 0)"; open $(OUT_SECURITY_FILE_HTML) && exit 1)

$(OUT_SAFETY_FILE_LOG): Makefile
	@\
		set -o pipefail ;\
		pipenv lock -r | pipenv run safety check --stdin --full-report | tee $(OUT_SAFETY_FILE_LOG) \
			|| (printf "$$(tput setaf 1)\n\nSecurity vulns found see: $(OUT_SAFETY_FILE_LOG)\n\n$$(tput sgr 0)"; exit 1)

$(OUT_DEPENDENCY_CHECK_FILE_HTML): Makefile
	@\
		DEPCHECK_DATA_DIR="$(DEPCHECK_DIR)/data" ;\
		DEPCHECK_REPORT_DIR="$(ARTIFACTS_SECURITY_PATH)" ;\
		mkdir -p $${DEPCHECK_DATA_DIR} $${DEPCHECK_REPORT_DIR} ;\
		sudo chown -R $(USER):$(USER) $${DEPCHECK_DATA_DIR} $${DEPCHECK_REPORT_DIR} ;\
		chmod -R 777 $${DEPCHECK_DATA_DIR} $${DEPCHECK_REPORT_DIR};\
		docker pull owasp/dependency-check:$(DEPCHECK_VERSION) ;\
		docker run --rm \
			--volume $(CURRENT_PATH):/src \
			--volume "$${DEPCHECK_DATA_DIR}":/usr/share/dependency-check/data \
			--volume "$${DEPCHECK_REPORT_DIR}":"$${DEPCHECK_REPORT_DIR}" \
			owasp/dependency-check:$(DEPCHECK_VERSION) \
				--scan /src \
				--project "$(PROJECT_NAME)" \
				--format HTML \
				--enableExperimental \
				--exclude **/.tox/** \
				--exclude **/.venv/** \
				--exclude **/__pycache__/** \
				--exclude **/.git/** \
				--out $(OUT_DEPENDENCY_CHECK_FILE_HTML) \
				--log $(OUT_DEPENDENCY_CHECK_FILE_LOG)

test-security: $(OUT_SECURITY_FILE_HTML) $(OUT_SAFETY_FILE_LOG) $(OUT_DEPENDENCY_CHECK_FILE_HTML)

test-depcheck: $(OUT_DEPENDENCY_CHECK_FILE_HTML)
	@open $(OUT_DEPENDENCY_CHECK_FILE_HTML)

test-coverage: test-unit
	@echo runnig test target and coverage

test-lint:
	@pipenv run prospector --profile .prospector.yaml

test: test-lint test-unit test-security

reports:
	@${MAKE} -i test-lint test-unit test-security
	@open $(OUT_UNIT_TEST_FILE_HTML)
	@open $(OUT_SECURITY_FILE_HTML)
	@open $(OUT_COVERAGE_FILE_HTML)/index.html
	@open $(OUT_SAFETY_FILE_LOG)
	@echo "Other reports:"
	@echo "    $(OUT_COVERAGE_FILE_XML)"
	@echo "    $(OUT_UNIT_TEST_FILE_XML)"
	@echo "Configuration files:"
	@echo "    $(OUT_COVERAGE_FILE_SETTINGS)"
	@echo "    $(OUT_PROSPECTOR_FILE_SETTINGS)"
	@echo "    $(OUT_BANDIT_FILE_SETTINGS)"

clean:
	@rm -fr  $(OUT_UNIT_TEST_FILE_XML) \
			 $(OUT_UNIT_TEST_FILE_HTML) \
			 $(OUT_COVERAGE_FILE_XML) \
			 $(OUT_COVERAGE_FILE_HTML) \
			 $(OUT_COVERAGE_FILE_SETTINGS) \
			 $(OUT_SECURITY_FILE_HTML) \
			 $(OUT_DEPENDENCY_CHECK_FILE_HTML) \
			 $(OUT_SAFETY_FILE_LOG) \
			 $(ARTIFACTS_DIST_PATH)
	@rm -vrf dist
	@rm -vrf deps
	@rm -vrf compute.egg-info
	@rm -vrf .pytest_cache
	@find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf
	@-rm -vf .coverage .coverage.*

clean-build:
	@echo "Cleaning compute build:"
	@rm -vrf compute.egg-info
	@rm -vrf dist
	@rm -fr $(ARTIFACTS_DIST_PATH)

build: clean-build _getdeps
	@pipenv run python setup.py sdist
	@mkdir -p $(ARTIFACTS_DIST_PATH)
	@cp -v dist/*.tar.gz $(ARTIFACTS_DIST_PATH)

build-pex:
	@pipenv run pex --interpreter-constraint=$(PEX_INTERPRETER_CONSTRAINT) --python-shebang=$(PEX_PYTHON_SHEBANG) $(ARTIFACTS_DIST_PATH)/$(PROJECT_NAME)*tar.gz  -e metamorphctl.cli:cli -o $(ARTIFACTS_DIST_PATH)/$(PROJECT_NAME) --disable-cache -vv

setupprj: _getdeps
	@pipenv install --dev

.PHONY: clean test test-unit test-coverage test-lint test-security build setupprj
