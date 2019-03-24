# Make this makefile self-documented with target `help`
.PHONY: help
.DEFAULT_GOAL := help

help:
	@grep -Eh '^[0-9a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

lint: ## Run all linters
	@black .

