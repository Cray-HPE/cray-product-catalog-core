#
# MIT License
#
# (C) Copyright 2020-2023 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
FROM artifactory.algol60.net/csm-docker/stable/docker.io/library/alpine:3.15 as base
RUN apk add --no-cache py3-pip python3
ARG PYMOD_VERSION=0.0.0

WORKDIR /src/
COPY cray_product_catalog/ ./cray_product_catalog

# The addition of the requirements-pyyaml.txt and requirements-non-pyyaml.txt files is to work around
# a problem installing the PyYAML Python module. A change was also made to the pip3 install commands to
# use these files. This work around essentially forces the install of the PyYAML module to use a
# version of Cython that is < 3.0 (this restriction was added to constraints.txt along with the changes
# here in the Dockerfile).
#
# These workarounds are necessary until one of the following things happens:
# * PyYAML publishes an update which constrains its build environment to using Cython < 3.0, so that
#   we don't have to manually impose that constraint.
# * A combination of Cython and PyYAML versions are released that allow PyYAML to build under Alpine using
#   Cython >= 3.0, so that we don't need to manually constrain the Cython version.
# * A PyYAML wheel is available for Alpine, so that the build environment is a non-issue.
#
# Currently there is a PyYAML PR up which would do the first item on that list: https://github.com/yaml/pyyaml/pull/702
# If that PR merges and is added to a PyYAML release, then the following steps should be done to undo the workaround:
#
# * Update constraints.txt with the PyYAML version that contains the workaround
# * Delete requirements-pyyaml.txt requirements-non-pyyaml.txt from the repository
# * Remove requirements-pyyaml.txt requirements-non-pyyaml.txt from the COPY line in this Dockerfile
# * Remove the Cython constraint from constraints.txt
# * Modify the following Dockerfile lines from:
#
#    && pip3 install --ignore-installed --no-cache-dir -r requirements-pyyaml.txt --no-build-isolation \
#    && pip3 install --ignore-installed --no-cache-dir -r requirements-non-pyyaml.txt \
#
#   to:
#
#    && pip3 install --ignore-installed --no-cache-dir -r requirements.txt \
#
COPY setup.py requirements.txt constraints.txt requirements-pyyaml.txt requirements-non-pyyaml.txt README.md ./
RUN echo ${PYMOD_VERSION} > .version

RUN apk add --upgrade --no-cache apk-tools \
    && apk update \
    && apk add --update --no-cache \
        gcc \
        python3-dev \
        libc-dev \
    && apk -U upgrade --no-cache \
    && pip3 install --upgrade pip wheel \
    && pip3 install --ignore-installed --no-cache-dir -r requirements-pyyaml.txt --no-build-isolation \
    && pip3 install --ignore-installed --no-cache-dir -r requirements-non-pyyaml.txt \
    && python3 setup.py install \
    && rm -rf /src/

# Must make catalog_update available as /catalog_update.py
# because it is currently specified this way in the cray-import-config helm
# chart. This is not easy to do with setuptools directly, so just link it
# here.
# https://github.com/Cray-HPE/cray-product-install-charts/blob/master/charts/cray-import-config/templates/job.yaml#L50
RUN ln -s /usr/bin/catalog_update /catalog_update.py

WORKDIR /
USER nobody:nobody

ENTRYPOINT [ "/usr/bin/catalog_update" ]
