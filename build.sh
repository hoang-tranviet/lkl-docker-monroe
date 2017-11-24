#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo $DIR
CONTAINER=${DIR##*/}
DOCKERFILE=${CONTAINER}.docker

# docker pull monroe/base
docker pull tranviethoang/lkl-base
docker build --rm --no-cache -f ${DOCKERFILE} -t ${CONTAINER} . && echo "Finished building ${CONTAINER}"
