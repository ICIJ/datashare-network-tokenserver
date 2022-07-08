CURRENT_VERSION ?= `pipenv run python setup.py --version`
DOCKER_NAME = datashare-network-tokenserver

clean:
		find . -name "*.pyc" -exec rm -rf {} \;
		rm -rf dist *.egg-info __pycache__

install: install_pip

install_pip:
		pipenv install -d

test:
		pipenv run pytest

run:
		pipenv run uvicorn tokenserver.main:app

genkey:
		pipenv run python tokenserver/gen_keypair.py

minor:
		pipenv run bumpversion --commit --tag --current-version ${CURRENT_VERSION} minor tokenserver/__init__.py

major:
		pipenv run bumpversion --commit --tag --current-version ${CURRENT_VERSION} major tokenserver/__init__.py

patch:
		pipenv run bumpversion --commit --tag --current-version ${CURRENT_VERSION} patch tokenserver/__init__.py

package:
		pipenv run python setup.py sdist bdist_wheel

distribute: package
		pipenv run twine upload dist/*

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
