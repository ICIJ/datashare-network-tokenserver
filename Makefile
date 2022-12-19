DOCKER_NAME = datashare-network-tokenserver
CURRENT_VERSION ?= `poetry version -s`
SEMVERS := major minor patch

clean:
		find . -name "*.pyc" -exec rm -rf {} \;
		rm -rf dist *.egg-info __pycache__

install: install_poetry

install_dev: install_poetry --with dev

install_poetry:
		poetry install

tests:
		poetry run pytest

run:
		poetry run uvicorn tokenserver.main:app

genkey:
		poetry run python tokenserver/gen_keypair.py

tag_version: 
		git commit -m "build: bump to ${CURRENT_VERSION}" pyproject.toml
		git tag ${CURRENT_VERSION}

$(SEMVERS):
		poetry version $@
		$(MAKE) tag_version
		
set_version:
		poetry version ${CURRENT_VERSION}
		$(MAKE) tag_version

package:
		poetry build

distribute:
		poetry publish --build

docker-publish: docker-build docker-tag docker-push

docker-run:
		docker run -it $(DOCKER_NAME)

docker-build: package
		docker build --build-arg VERSION=$(CURRENT_VERSION) -t $(DOCKER_NAME) .

docker-tag:
		docker tag $(DOCKER_NAME) $(DOCKER_USER)/$(DOCKER_NAME):${CURRENT_VERSION}
		docker tag $(DOCKER_NAME) $(DOCKER_USER)/$(DOCKER_NAME):latest

docker-push:
		docker push $(DOCKER_USER)/$(DOCKER_NAME):${CURRENT_VERSION}
		docker push $(DOCKER_USER)/$(DOCKER_NAME):latest
