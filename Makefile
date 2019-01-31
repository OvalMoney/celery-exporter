.PHONY: help
.DEFAULT_GOAL := help

DOCKER_REPO="ovalmoney/celery-exporter"
DOCKER_VERSION="latest"

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

all: clean docker_build ## Clean and Build

clean: ## Clean folders
	rm -rf dist/ *.egg-info

docker_build: ## Build Docker file
	export DOCKER_REPO
	export DOCKER_VERSION

	docker build \
		--build-arg DOCKER_REPO=${DOCKER_REPO} \
		--build-arg VERSION=${DOCKER_VERSION} \
		--build-arg VCS_REF=`git rev-parse --short HEAD` \
		--build-arg BUILD_DATE=`date -u +”%Y-%m-%dT%H:%M:%SZ”` \
		-f ./Dockerfile \
		-t ${DOCKER_REPO}:${DOCKER_VERSION} \
		.

help: ## Print this help
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)
          
