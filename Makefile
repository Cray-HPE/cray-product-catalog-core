#
# MIT License
#
# (C) Copyright 2021-2024 Hewlett Packard Enterprise Development LP
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

# If you wish to perform a local build, you will need to clone or copy the contents of the
# cms-meta-tools repo to ./cms_meta_tools

NAME ?= cray-product-catalog
PY_VERSION ?= 3.6
VENV_DIR ?= pylint$(PY_VERSION)
VENV_PY ?= $(VENV_DIR)/bin/python

all: runbuildprep lint pymod
pymod: pymod_prepare pymod_build pymod_test

runbuildprep:
		./cms_meta_tools/scripts/runBuildPrep.sh

lint:
		./cms_meta_tools/scripts/runLint.sh

pymod_prepare:
		pip3 install --upgrade --user pip setuptools wheel

pymod_build:
		python3 setup.py sdist bdist_wheel

pymod_test:
		python3 --version
		python3 -m venv --system-site-packages $(VENV_DIR)
		$(VENV_PY) --version
		$(VENV_PY) -m pip install -r requirements.txt
		$(VENV_PY) -m pip install -r requirements-test.txt
		$(VENV_PY) setup.py install
		$(VENV_PY) -m unittest discover tests
		$(VENV_PY) -m pycodestyle --config=.pycodestyle cray_product_catalog tests
		# Run pylint, but only fail the build if the code scores lower than 8.0
		$(VENV_PY) -m pylint --fail-under=8.0 --rcfile=.pylintrc cray_product_catalog tests
