# ====================================================================================
# Variables

## General Variables
# Branch Variables
PROTECTED_BRANCH := main
CURRENT_BRANCH   := $(shell git rev-parse --abbrev-ref HEAD)
# Use repository name as application name
APP_NAME    := app
# Get current commit
APP_COMMIT  := $(shell git log --pretty=format:'%h' -n 1)
# Check if tag name is set, if yes use set value, removing leading v.
# Else use app commit, prepended by dev-.
IMAGE_TAG   ?= ""
NORMALIZED_TAG = $(shell if [[ ${IMAGE_TAG} == v* ]]; then echo "$(shell echo $(IMAGE_TAG) | cut -d 'v' -f 2)"; else echo $(IMAGE_TAG) ; fi)
APP_VERSION = $(shell if [ -z "${NORMALIZED_TAG}" ]; then echo dev-$(APP_COMMIT); else echo $(NORMALIZED_TAG) ; fi)

## General Configuration Variables
# We don't need make's built-in rules.
MAKEFLAGS     += --no-builtin-rules
# Be pedantic about undefined variables.
MAKEFLAGS     += --warn-undefined-variables
# Set help as default target
.DEFAULT_GOAL := help

## Docker Variables

# Docker executable
DOCKER                  := $(shell which docker)
# Dockerfile's location
DOCKER_FILE             += ./docker/Dockerfile
# Docker compose file
DOCKER_COMPOSE_FILE     += ./docker/docker-compose.yml

# Docker compose file for dependencies
DOCKER_COMPOSE_DEPS_FILE += ./docker/docker-compose-dependencies.yml

# Docker compose file for score
DOCKER_COMPOSE_SCORE_FILE += ./docker/docker-compose-score.yml

# Docker options to inherit for all docker run commands
DOCKER_OPTS             += --rm -u $$(id -u):$$(id -g) --platform "linux/amd64"


## Docker Build Variables
# Python/uv base image
DOCKER_IMAGE_PYTHON     += "astral/uv:0.12.19-python3.13-trixie-slim@sha256:aba5f865793af9275ceaa06d30935dfc6db8b81969c9fb099b0ebca6396b189e"
DOCKER_IMAGE_DOCKERLINT += "hadolint/hadolint:v2.15.1@sha256:32dac94127fd60b7b7e3fbfc65e1383b9b5e25c9bfd7b8536de7a539fe68a12d"

## Python Variables
# Python executable
PYTHON                       := $(shell which python)
# UV executable
UV                           := $(shell which uv)
# UV options
UV_OPTS                      ?=


# ====================================================================================
# Colors

BLUE   := $(shell printf "\033[34m")
YELLOW := $(shell printf "\033[33m")
RED    := $(shell printf "\033[31m")
GREEN  := $(shell printf "\033[32m")
CYAN   := $(shell printf "\033[36m")
CNone  := $(shell printf "\033[0m")

# ====================================================================================
# Logger

TIME_SHORT	= `date +%H:%M:%S`
TIME		= $(TIME_SHORT)

INFO = echo ${TIME} ${BLUE}[ .. ]${CNone}
WARN = echo ${TIME} ${YELLOW}[WARN]${CNone}
ERR  = echo ${TIME} ${RED}[FAIL]${CNone}
OK   = echo ${TIME} ${GREEN}[ OK ]${CNone}
FAIL = (echo ${TIME} ${RED}[FAIL]${CNone} && false)

# ====================================================================================
# Verbosity control hack

VERBOSE ?= 0
AT_0 := @
AT_1 :=
AT = $(AT_$(VERBOSE))

# ====================================================================================
# Targets

help: ## to get help
	$(AT)echo "Welcome to ${APP_NAME}:${APP_VERSION}"
	$(AT)echo "Usage:"
	$(AT)grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) |\
	awk 'BEGIN {FS = ":.*?## "}; {printf "make ${CYAN}%-30s${CNone} %s\n", $$1, $$2}'

.PHONY: python-test
python-test: ## to run python tests
	$(AT)$(INFO) testing python...
	$(AT)$(UV) run coverage run -m pytest || ${FAIL}
	${AT}$(UV) run coverage combine
	${AT}$(UV) run coverage report
	${AT}$(UV) run coverage html
	$(AT)$(OK) testing python

.PHONY: python-lint
python-lint: ## to run linters on python code
	$(AT)$(INFO) python lint...
	$(AT)$(UV) run ruff check . || ${FAIL}
	$(AT)$(UV) run ruff format --check || ${FAIL}
	$(AT)$(UV) run mypy app --check || ${FAIL}


.PHONY: python-licensecheck
python-licensecheck: ## to check licenses of dependencies
	$(AT)$(INFO) python dependency license check...
	$(AT)$(UV) run licensecheck --format ansi \
	--ignore-license mpl \
	--only-licenses apache bsd isc mit mpl python unlicense \
	--fail-licenses gpl \
	--show-only-failing \
	--zero || ${FAIL}
	$(AT)$(OK) checking dependency licenses


.PHONY: docker-build
docker-build: ## to build the docker image
	@$(INFO) Performing Docker build ${APP_NAME}:${APP_VERSION}
	$(AT)$(DOCKER) build \
	--build-arg PYTHON_IMAGE=${DOCKER_IMAGE_PYTHON} \
	--build-arg APP_NAME=${APP_NAME} \
	-f ${DOCKER_FILE} . \
	-t ${APP_NAME}:${APP_VERSION} \
	-t ${APP_NAME}:latest
	@$(OK) Performing Docker build ${APP_NAME}:${APP_VERSION}

.PHONY: docker-lint
docker-lint: ## to lint the Dockerfile
	@$(INFO) Dockerfile linting...
	$(AT)$(DOCKER) run -i ${DOCKER_OPTS} \
	${DOCKER_IMAGE_DOCKERLINT} \
	< ${DOCKER_FILE} || ${FAIL}
	@$(OK) Dockerfile linting

.PHONY: start-deps
start-deps: ## to start dependencies only in a containerized environment
	$(AT)$(INFO) Running ${CYAN}${APP_NAME}${CNone} dependencies...
	$(AT)$(DOCKER) compose -f ${DOCKER_COMPOSE_DEPS_FILE} up -d --build --remove-orphans --wait || ${FAIL}
	$(AT)$(OK) Started dependencies in docker compose

.PHONY: stop-deps
stop-deps: ## to stop dependencies running in containerized environment
	$(AT)$(INFO) Stopping ${CYAN}${APP_NAME}${CNone} dependencies...
	$(AT)$(DOCKER) compose -f ${DOCKER_COMPOSE_DEPS_FILE} down --remove-orphans|| ${FAIL}
	$(AT)$(OK) Stopped dependencies in docker compose

.PHONY: start
start: ## to start app and dependencies in a containerized environment
	$(AT)$(INFO) Running ${CYAN}${APP_NAME}${CNone}...
	$(AT)$(DOCKER) compose -f ${DOCKER_COMPOSE_FILE} up -d --build --remove-orphans --wait || ${FAIL}
	$(AT)$(OK) Started app in docker compose

.PHONY: start-develop
start-develop: ## to start app and dependencies in a containerized development environment
	$(AT)$(INFO) Running ${CYAN}${APP_NAME}${CNone}...
	$(AT)$(DOCKER) compose -f ${DOCKER_COMPOSE_FILE} up --build --remove-orphans || ${FAIL}
	$(AT)$(OK) Started app in docker compose

.PHONY: stop
stop: ## to stop containerized environment
	$(AT)$(INFO) Stopping ${CYAN}${APP_NAME}${CNone}...
	$(AT)$(DOCKER) compose -f ${DOCKER_COMPOSE_FILE} down --remove-orphans|| ${FAIL}
	$(AT)$(OK) Stopped app in docker compose
