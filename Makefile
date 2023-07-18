RELEASE_NAME=mlops-fastapi
IMAGE_NAME=ACRFIQUANTITPROD001.AZURECR.IO/${RELEASE_NAME}
SHA:=$(if $(SHA),$(SHA),$(shell git rev-parse --short HEAD))
REPO_NAME=$(shell git config --get remote.origin.url | sed 's/.*\/\([^ ]*\/[^.]*\).*/\1/' | sed -e "s/\//-/g")
BRANCH_NAME=$(shell git rev-parse --abbrev-ref HEAD)

FULL_IMAGE_TAG_RAW:=$(IMAGE_NAME):${REPO_NAME}-${BRANCH_NAME}-gc-${SHA}
FULL_IMAGE_TAG:=$(shell echo $(FULL_IMAGE_TAG_RAW) | tr A-Z a-z)

OVERWRITE_IMAGE_TAG:=$(IMAGE_NAME):latest
SCAN_IMAGE_TAG:=$(RELEASE_NAME):latest
BUILD_ENV:=$(if $(BUILD_ENV),$(BUILD_ENV),dev)

CLUSTER_NAME=aks-cortex-prod-003
CLUSTER_NAMESPACE=fiquantit-prod
DEPLOYMENT_SERVICE_NAME=mlops-fastapi

build:
	$(info FULL_IMAGE_TAG=${FULL_IMAGE_TAG}...)
	$(info $(shell git log --oneline | tac | tail -1))
	docker build -t '${FULL_IMAGE_TAG}' . --no-cache
	docker tag '${FULL_IMAGE_TAG}' '${OVERWRITE_IMAGE_TAG}'
	docker tag '${FULL_IMAGE_TAG}' '${SCAN_IMAGE_TAG}'

test:
	docker run -i --entrypoint sh '${FULL_IMAGE_TAG}' /tests.sh

push:
	docker push '${FULL_IMAGE_TAG}'
	docker push '${OVERWRITE_IMAGE_TAG}'

deploy_aks:
	whoami
	kubectl --context="${CLUSTER_NAME}" delete service ${DEPLOYMENT_SERVICE_NAME} -n fiquantit-prod
	kubectl --context="${CLUSTER_NAME}" delete deployments ${DEPLOYMENT_SERVICE_NAME} -n fiquantit-prod
	kubectl --context="${CLUSTER_NAME}" delete ingress ${DEPLOYMENT_SERVICE_NAME} -n fiquantit-prod
	kubectl --context="${CLUSTER_NAME}" -n fiquantit-prod apply -f ./deploy/values.yaml
