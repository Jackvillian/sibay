IMGTAG=$(arg1)
GITTAG=$(arg2)

.PHONY:
help:
	@echo ""
	@echo "Подсказка"
	@echo ""
	@echo "Создание образа докера:"
	@echo "    make docker_build"
	@echo ""
	@echo "Cоздание релиза:"
	@echo "    make release"
	@echo ""
	@echo "Запуск деплоя:"
	@echo "    make deploy_release"
	@echo ""
	@echo "Запуск деплоя из master:"
	@echo "    make deploy_master"
	@echo ""
	@echo "dev среда"
	@echo ""
	@echo "Запуск миграции:"
	@echo "    make migrate"
	@echo ""
	@echo "Запуск Celery:"
	@echo "    make run_celery"
	@echo ""

.PHONY:
docker_build:
	@echo ""
	@echo "Building docker images..."
	@sh scripts/build.sh $(IMGTAG)
	@cat /dev/null > ansible/vars/tags.yml
	@echo "---" >> ansible/vars/tags.yml
	@echo "tag: $(IMGTAG)" >> ansible/vars/tags.yml
	@echo "created images tag $(IMGTAG)"

.PHONY:
release:
	@echo ""
	@echo "release ..."
	@sh scripts/release.sh $(GITTAG)

.PHONY:
deploy_release:
	@echo ""
	@echo "deploying ..."
	@cd ansible && ansible-playbook deploy.yml  -i inventory/hosts -e branch=release

.PHONY:
deploy_master:
	@echo ""
	@echo "deploying ..."
	@cd ansible && ansible-playbook deploy.yml  -i inventory/hosts -e branch=master

.PHONY:
migrate:
	@echo ""
	@echo "run migrations for Dev"
	@sh scripts/run_migrations.sh

.PHONY:
run_celery:
	@echo ""
	@echo "run celery for DEV"

