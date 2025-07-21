# MIT License
#
# (C) Copyright 2021-2025 Hewlett Packard Enterprise Development LP
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

"""
Defines classes for querying for information about the installed products.
"""
from collections import defaultdict
import logging
from pkg_resources import parse_version
import warnings

from jsonschema.exceptions import ValidationError
from kubernetes.client import CoreV1Api
from kubernetes.client.rest import ApiException
from kubernetes.config import ConfigException
from urllib3.exceptions import MaxRetryError
from yaml import safe_load, YAMLError

from cray_product_catalog.constants import (
    COMPONENT_DOCKER_KEY,
    COMPONENT_HELM,
    COMPONENT_S3,
    COMPONENT_MANIFESTS,
    COMPONENT_REPOS_KEY,
    COMPONENT_VERSIONS_PRODUCT_MAP_KEY,
    PRODUCT_CATALOG_CONFIG_MAP_NAME,
    PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
    PRODUCT_CATALOG_CONFIG_MAP_LABEL_STR
)
from cray_product_catalog.schema.validate import get_validator
from cray_product_catalog.util import cached_property, load_k8s
from cray_product_catalog.util.merge_dict import merge_dict

LOGGER = logging.getLogger(__name__)


class ProductCatalogError(Exception):
    """An error occurred reading or manipulating product installs."""


class ProductCatalog:
    """A collection of installed product versions.

    Attributes:
        name (str): The product catalog Kubernetes ConfigMap name.
        namespace (str): The product catalog Kubernetes ConfigMap namespace.
        products ([InstalledProductVersion]): A list of installed product
            versions.
    """
    @staticmethod
    def _get_k8s_api():
        """Load a Kubernetes CoreV1Api and return it.

        Returns:
            CoreV1Api: The Kubernetes API.

        Raises:
            ProductCatalogError: if there was an error loading the
                Kubernetes configuration.
        """
        try:
            load_k8s()
            return CoreV1Api()
        except ConfigException as err:
            raise ProductCatalogError(f'Unable to load kubernetes configuration: {err}.') from err

    def __init__(self, name=PRODUCT_CATALOG_CONFIG_MAP_NAME, namespace=PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                 shallow=False):
        """Create the ProductCatalog object.

        Args:
            name (str): The product catalog Kubernetes ConfigMap name.
            namespace (str): The product catalog Kubernetes ConfigMap namespace.
            shallow (bool): If True, only load product catalog data from the main
                ConfigMap, not from any of the product-specific ConfigMaps. Note
                that any data under the component_versions key stored in the
                product-specific ConfigMaps will not be loaded, and warnings will
                be logged if there is an attempt to access that data.

        Raises:
            ProductCatalogError: if reading the ConfigMap failed.
        """
        self.name = name
        self.namespace = namespace
        self.k8s_client = self._get_k8s_api()
        self.shallow = shallow

        # Create a single instance of the schema validator. The same validator can be
        # used for all versions of all products. This reduces the number of times we
        # need to load the schema and validate it against the JSON schema meta-schema.
        self.validator = get_validator()

        config_map_data = self._get_config_map_data()
        self.products = [
            InstalledProductVersion(product_name, product_version, product_version_data,
                                    validator=self.validator, shallow=self.shallow)
            for product_name, product_data in config_map_data.items()
            for product_version, product_version_data in product_data.items()
        ]

        invalid_products = [
            str(p) for p in self.products if not p.is_valid
        ]
        if invalid_products:
            LOGGER.warning(
                'The following products have product catalog data that is not valid against the expected schema: %s',
                ", ".join(invalid_products)
            )

        self.products = [
            p for p in self.products if p.is_valid
        ]

    def _get_config_maps(self):
        """Get the ConfigMaps containing product catalog data from Kubernetes.

        This finds and returns all ConfigMaps that have the new label
        PRODUCT_CATALOG_CONFIG_MAP_LABEL_STR. If no such ConfigMaps are found,
        it falls back on the legacy ConfigMap with the name specified in the
        constructor.

        Raises:
            ProductCatalogError: if there is a failure to query Kubernetes for
                the ConfigMaps or if the single ConfigMap contains no data.

        Returns:
            list: A list of V1ConfigMap objects that contain product catalog data.
        """
        try:
            config_maps = self.k8s_client.list_namespaced_config_map(
                self.namespace, label_selector=PRODUCT_CATALOG_CONFIG_MAP_LABEL_STR
            ).items
        except MaxRetryError as err:
            raise ProductCatalogError(
                f'Unable to connect to Kubernetes to read ConfigMaps in {self.namespace} namespace: {err}'
            ) from err
        except ApiException as err:
            # The full string representation of ApiException is very long, so just log err.reason
            raise ProductCatalogError(
                f'Error listing ConfigMaps in {self.namespace} namespace: {err.reason}'
            ) from err

        if len(config_maps) == 0:
            LOGGER.info('No ConfigMaps found with label "%s" in namespace "%s". '
                        'Falling back on ConfigMap %s/%s',
                        PRODUCT_CATALOG_CONFIG_MAP_LABEL_STR,
                        self.namespace, self.namespace, self.name)
            try:
                config_map = self.k8s_client.read_namespaced_config_map(self.name, self.namespace)
            except MaxRetryError as err:
                raise ProductCatalogError(
                    f'Unable to connect to Kubernetes to read {self.namespace}/{self.name} ConfigMap: {err}'
                ) from err
            except ApiException as err:
                raise ProductCatalogError(
                    f'Error reading {self.namespace}/{self.name} ConfigMap: {err.reason}'
                ) from err
            if config_map.data is None:
                raise ProductCatalogError(
                    f'No data found in {self.namespace}/{self.name} ConfigMap.'
                )
            config_maps = [config_map]

        return config_maps

    def _get_config_map_data(self):
        """Load product catalog data from the cray-product-catalog ConfigMaps.

        This finds and merges data from all ConfigMaps that have the new label
        PRODUCT_CATALOG_CONFIG_MAP_LABEL_STR or from the legacy ConfigMap with
        the name specified in the constructor if no labeled ConfigMaps are found.

        Raises:
            ProductCatalogError: if there is a failure to load data from the
                ConfigMap

        Returns:
            dict: A mapping from product name to another dict mapping from
                product versions to the data for that product version.
        """
        config_maps = self._get_config_maps()
        config_map_data = defaultdict(dict)
        for cm in config_maps:
            cm_name = cm.metadata.name
            if self.shallow and cm_name != self.name or not cm_name.startswith(self.name):
                # Skip if shallow and not the main config map or if the ConfigMap name
                # does not start with the expected prefix.
                continue
            for product_name, product_data_str in cm.data.items():
                try:
                    product_data = safe_load(product_data_str)
                except YAMLError as err:
                    raise ProductCatalogError(
                        f'Failed to load data for product "{product_name}" from ConfigMap {cm_name}: {err}'
                    ) from err

                config_map_data[product_name] = merge_dict(product_data, config_map_data[product_name])

        return dict(config_map_data)

    def get_product(self, name, version=None):
        """Get the InstalledProductVersion matching the given name/version.

        Args:
            name (str): The product name.
            version (str, optional): The product version. If omitted or None,
                get the latest installed version.

        Returns:
            An InstalledProductVersion with the given name and version.

        Raises:
            ProductCatalogError: If there is more than one matching
                InstalledProductVersion, or if there are none.
        """
        if not version:
            matching_name_products = [product for product in self.products if product.name == name]
            if not matching_name_products:
                raise ProductCatalogError(f'No installed products with name {name}.')
            latest = sorted(matching_name_products,
                            key=lambda p: parse_version(p.version))[-1]
            LOGGER.debug('Using latest version (%s) of product %s', latest.version, name)
            return latest

        matching_products = [
            product for product in self.products
            if product.name == name and product.version == version
        ]
        if not matching_products:
            raise ProductCatalogError(
                f'No installed products with name {name} and version {version}.'
            )
        if len(matching_products) > 1:
            raise ProductCatalogError(
                f'Multiple installed products with name {name} and version {version}.'
            )

        return matching_products[0]


def load_cm_data(config_map):
    """Parse read_namespaced_config_map output and get array of InstalledProductVersion objects.

    Args:
        config_map (V1ConfigMap): ConfigMap object

    Returns:
        An array of InstalledProductVersion objects.
    """
    warnings.warn(
        "The 'load_cm_data' function is deprecated and will be removed in a future version of this library.",
        DeprecationWarning,
        stacklevel=2
    )
    return [
        InstalledProductVersion(product_name, product_version, product_version_data)
        for product_name, product_versions in config_map.data.items()
        for product_version, product_version_data in safe_load(product_versions).items()
    ]


def load_config_map_data(name, configmaps):
    """Parse list_namespaced_config_map output and get array of InstalledProductVersion objects.

    Args:
        name: Main ConfigMap name with which all product ConfigMaps name starts
        configmaps (V1ConfigMapList): list of ConfigMap objects.

    Returns:
        An array of InstalledProductVersion objects.
    """
    warnings.warn(
        "The 'load_config_map_data' function is deprecated and will be removed in a future version of this library.",
        DeprecationWarning,
        stacklevel=2
    )
    config_map_data = {}
    for cm in configmaps:
        if not cm.metadata.name.startswith(name):
            continue
        for product_name, product_versions in cm.data.items():
            for product_version, product_version_data in safe_load(product_versions).items():
                cm_key = product_name + ':' + product_version
                if cm_key in config_map_data:
                    config_map_data[cm_key] = merge_dict(config_map_data[cm_key], product_version_data)
                else:
                    config_map_data[cm_key] = product_version_data
    return [
        InstalledProductVersion(key.split(':',)[0], key.split(':')[1], product_version_data)
        for key, product_version_data in config_map_data.items()
    ]


class InstalledProductVersion:
    """A representation of a version of a product that is currently installed.

    Attributes:
        name (str): The product name.
        version (str): The product version.
        data (dict): A dictionary representing the data within a given product and
            version in the product catalog, which is expected to contain a
            'component_versions' key that will point to the respective
            versions of product components, e.g. Docker images.
        validator (jsonschema.protocols.Validator): A JSON schema validator for the
            product version data. If None, a validator is created from the product
            catalog schema file.
        shallow (bool): If True, the product version data only includes data from
            the main product ConfigMap, not from any of the product-specific ConfigMaps.
            A warning will be logged any time `component_versions` data is accessed.
    """
    def __init__(self, name, version, data, validator=None, shallow=False):
        self.name = name
        self.version = version
        self.data = data
        self.validator = validator or get_validator()
        self.shallow = shallow

    def __str__(self):
        return f'{self.name}-{self.version}'

    @cached_property
    def is_valid(self):
        """bool: True if this product's version data fits the schema."""
        try:
            self.validator.validate(self.data)
            return True
        except ValidationError:
            return False

    @property
    def component_data(self):
        """dict: a mapping from types of components to lists of components"""
        if self.shallow:
            LOGGER.warning('Data from "component_versions" may be incomplete due to shallow loading.')
        return self.data.get(COMPONENT_VERSIONS_PRODUCT_MAP_KEY, {})

    @property
    def docker_images(self):
        """Get Docker images associated with this InstalledProductVersion.

        Returns:
            A list of tuples of (image_name, image_version)
        """
        return [(component['name'], component['version'])
                for component in self.component_data.get(COMPONENT_DOCKER_KEY) or []]

    @property
    def helm_charts(self):
        """Get Helm charts associated with this InstalledProductVersion.

        Returns:
            A list of tuples of (chart_name, chart_version)
        """
        return [(component['name'], component['version'])
                for component in self.component_data.get(COMPONENT_HELM) or []]

    @property
    def s3_artifacts(self):
        """Get S3 artifacts associated with this InstalledProductVersion.

        Returns:
            A list of tuples of (artifact bucket, artifact key)
        """
        return [(component['bucket'], component['key'])
                for component in self.component_data.get(COMPONENT_S3) or []]

    @property
    def loftsman_manifests(self):
        """Get Loftsman manifests associated with this InstalledProductVersion.

        Returns:
            A list of manifests
        """
        return self.component_data.get(COMPONENT_MANIFESTS, [])

    @property
    def repositories(self):
        """list of dict: the repositories for this product version."""
        return self.component_data.get(COMPONENT_REPOS_KEY, [])

    @property
    def group_repositories(self):
        """list of dict: the group-type repositories for this product version."""
        return [repo for repo in self.repositories if repo.get('type') == 'group']

    @property
    def hosted_repositories(self):
        """list of dict: the hosted-type repositories for this product version."""
        return [repo for repo in self.repositories if repo.get('type') == 'hosted']

    @property
    def hosted_and_member_repo_names(self):
        """set of str: all hosted repository names for this product version

        This includes all explicitly listed hosted repos plus any hosted repos
        which are listed only as members of any of the group repos
        """
        # Get all hosted repositories, plus any repos that might be under a group repo's "members" list.
        repository_names = set(repo.get('name') for repo in self.hosted_repositories)
        for group_repo in self.group_repositories:
            repository_names |= set(group_repo.get('members'))

        return repository_names

    @property
    def configuration(self):
        """dict: information about the config management repo for the product"""
        return self.data.get('configuration', {})

    @property
    def clone_url(self):
        """str or None: the clone url of the config repo for the product, if available."""
        return self.configuration.get('clone_url')

    @property
    def commit(self):
        """str or None: the commit hash of the config repo for the product, if available."""
        return self.configuration.get('commit')

    @property
    def import_branch(self):
        """str or None: the branch name of the config repo for the product, if available."""
        return self.configuration.get('import_branch')

    def _get_ims_resources(self, ims_resource_type):
        """Get IMS resources (images or recipes) provided by the product

        Args:
            ims_resource_type (str): Either 'images' or 'recipes'

        Returns:
            list of dict: the IMS resources of the given type provided by the
                product. Each has a 'name' and 'id' key.

        Raises:
            ValueError: if given an unrecognized `ims_resource_type`
        """
        if ims_resource_type not in ('recipes', 'images'):
            raise ValueError(f'Unrecognized IMS resource type "{ims_resource_type}"')

        ims_resource_data = self.data.get(ims_resource_type) or {}

        return [
            {'name': resource_name, 'id': resource_data.get('id')}
            for resource_name, resource_data in ims_resource_data.items()
        ]

    @property
    def images(self):
        """list of dict: the list of images provided by this product"""
        return self._get_ims_resources('images')

    @property
    def recipes(self):
        """list of dict: the list of recipes provided by this product"""
        return self._get_ims_resources('recipes')

    @property
    def supports_active(self):
        """bool: whether this product version indicates whether or not it is the active version"""
        return 'active' in self.data

    @property
    def active(self):
        """bool: whether or not this product is active"""
        return self.data.get('active', False)
