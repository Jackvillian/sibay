# Maki version: master
# Maki template version: 1.0
SHELL=/bin/bash

# common
common_build_args=--volume ssh-agent:/ssh-agent \
					--env SSH_AUTH_SOCK=/ssh-agent/ssh-agent.sock \
					--env FIXUID=$$(id -u) \
					--env FIXGID=$$(id -g) \
					--env HOME=/home/docker \
					--user $$(id -u):$$(id -g)

# Components variables
## backend
backend_path=.
backend_build_image=feedback2-app-backend:build
## frontend
frontend_path=.
frontend_build_image=registry.mos-team.ru/mosru/node:8-1.1.12

# build-dev meta target
.PHONY: build
build: ## dev: Сборка всех компонентов
build: build-docker-dev build-backend-dev build-frontend-dev

# build-deploy meta target
.PHONY: build-deploy
build-deploy: ## deploy: Сборка всех компонентов
build-deploy: build-docker-deploy build-backend-deploy build-frontend-deploy


.PHONY: build-docker-dev
build-docker-dev: ## dev: Сборка Docker образов
	@if [ ! -f .env ] && [ -f .env.dist ]; then cp -v .env.dist .env ; fi
	@docker-compose build --pull \
						--build-arg YUM_EXTRA_PACKAGES="php-xml php-intl php-mbstring php-xdebug"
.PHONY: build-docker-deploy
build-docker-deploy: ## deploy: Сборка Docker образов
	@docker build . \
				--file .deploy/docker/backend/Dockerfile \
				--pull \
				--tag registry.mos-team.ru/mosru/feedback2-app-backend:${BRANCH_NAME}-${BUILD_NUMBER} \
				--tag feedback2-app-backend:build \
				--build-arg YUM_EXTRA_PACKAGES="php-xml php-intl php-mbstring"
	@docker build . \
				--file .deploy/docker/frontend/Dockerfile \
				--pull \
				--tag registry.mos-team.ru/mosru/feedback2-app-frontend:${BRANCH_NAME}-${BUILD_NUMBER} \


.PHONY: push-docker
push-docker: ## deploy: Отправить Docker образы в Registry
	@docker push registry.mos-team.ru/mosru/feedback2-app-backend:${BRANCH_NAME}-${BUILD_NUMBER}
	@docker push registry.mos-team.ru/mosru/feedback2-app-frontend:${BRANCH_NAME}-${BUILD_NUMBER}

# Clean meta target
.PHONY: clean
clean: ## Полная очистка проекта от временных файлов, Docker контейнеров и образов
clean: clean-docker clean-backend clean-frontend


.PHONY: clean-docker
clean-docker: ## Остановка и очистка Docker образов, контейнеров и данных
	@if [ ! -f .env ] && [ -f .env.dist ]; then cp -v .env.dist .env ; fi
	@docker-compose down --volumes --remove-orphans --rmi local

# Components targets
.PHONY: build-backend-dev
build-backend-dev: ## Сборка компонента backend
	@if [ ! -n "${JENKINS}" ]; then ssh-add -l ; fi
	@if [ ! -n "${JENKINS}" ]; then pinata-ssh-forward > /dev/null ; fi
	@docker run --rm $$(if [ ! -n "${JENKINS}" ]; then echo "-it" ; else echo "--env SSH_PROXY=${SSH_PROXY}" ; fi) \
				$(common_build_args) \
				-v $(PWD)/$(backend_path):/app \
				$(backend_build_image) \
				bash -c "composer install --prefer-dist --no-interaction --no-scripts --no-progress"

.PHONY: build-backend-deploy
build-backend-deploy: ## Сборка компонента backend
	@docker run --rm \
				$(common_build_args) \
				--env SSH_PROXY=${SSH_PROXY} \
				-v $(PWD)/$(backend_path):/app \
				$(backend_build_image) \
				bash -c "composer install --prefer-dist --no-interaction --no-scripts --no-progress --no-dev --optimize-autoloader --classmap-authoritative"

.PHONY: clean-backend
clean-backend: ## Очистка временных файлов компонента backend
	@rm -rf "./vendor"
	@rm -rf "./var/cache"
	@rm -rf "./var/log"

.PHONY: backend-composer-install
backend-composer-install:
	@docker run --rm \
				$(common_build_args) \
				-v $(PWD)/$(backend_path):/app \
				$(backend_build_image) \
				bash -c "composer install"

.PHONY: backend-composer-validate
backend-composer-validate:
	@docker run --rm \
				$(common_build_args) \
				-v $(PWD)/$(backend_path):/app \
				$(backend_build_image) \
				bash -c "composer validate --strict"

.PHONY: backend-phiremock
backend-phiremock:
	@docker run --rm \
				$(common_build_args) \
				-v $(PWD)/$(backend_path):/app \
				$(backend_build_image) \
				bash -c "vendor/bin/phiremock -e /app/.phiremock/"

.PHONY: build-frontend-dev
build-frontend-dev: ## Сборка компонента frontend
	@if [ ! -n "${JENKINS}" ]; then ssh-add -l ; fi
	@if [ ! -n "${JENKINS}" ]; then pinata-ssh-forward > /dev/null ; fi
	@docker run --rm $$(if [ ! -n "${JENKINS}" ]; then echo "-it" ; else echo "--env SSH_PROXY=${SSH_PROXY}" ; fi) \
				$(common_build_args) \
				-v $(PWD)/$(frontend_path):/app \
				$(frontend_build_image) \
				bash -c "yarn install && yarn build"

.PHONY: build-frontend-deploy
build-frontend-deploy: ## Сборка компонента frontend
	@docker run --rm \
				$(common_build_args) \
				--env SSH_PROXY=${SSH_PROXY} \
				-v $(PWD)/$(frontend_path):/app \
				$(frontend_build_image) \
				bash -c "yarn install && yarn build"

.PHONY: clean-frontend
clean-frontend: ## Очистка временных файлов компонента frontend
	@rm -rf "./public/build"
	@rm -rf "./node_modules"


.PHONY: start
start: ## Создаем виртуальную сеть и запускаем контейнеры в интерактивном режиме.
	@docker network create --attachable --subnet=172.33.0.0/16 mosru || true
	@FIXUID=$$(id -u) FIXGID=$$(id -g) docker-compose up

.PHONY: stop
stop: ## Останавливаем контейнеры (применимо когда контейнеры были запущены в фоновом режиме).
	@docker-compose stop

.PHONY: help
help: ## Отобразить данное сообщение.
	@cat $(MAKEFILE_LIST) | grep -e "^[a-zA-Z_\-]*: *.*## *" | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
