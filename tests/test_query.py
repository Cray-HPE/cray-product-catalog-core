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
#

"""
Unit tests for cray_product_catalog.query module
"""

import copy
import logging
import unittest
from unittest.mock import Mock, patch

from kubernetes.client import V1ConfigMap, V1ConfigMapList, V1ObjectMeta
from kubernetes.config import ConfigException
from yaml import safe_dump

from cray_product_catalog.constants import (
    PRODUCT_CATALOG_CONFIG_MAP_LABEL_STR, PRODUCT_CATALOG_CONFIG_MAP_NAME
)
from cray_product_catalog.query import InstalledProductVersion, ProductCatalog, ProductCatalogError
from tests.mocks import (
    COS_VERSIONS, CPE_VERSION, MOCK_COMBINED_PRODUCT_CATALOG_CONFIG_MAP, MOCK_EMPTY_LABELED_PRODUCT_CATALOG_CONFIG_MAPS,
    MOCK_INVALID_PRODUCT_DATA, MOCK_LABELED_PRODUCT_CATALOG_CONFIG_MAPS, MOCK_MAIN_PRODUCT_CATALOG_CONFIG_MAP,
    MOCK_MAIN_PRODUCT_CATALOG_DATA, MOCK_NAMESPACE, OTHER_PRODUCT_VERSION, SAT_SEPARATE_CM_DATA, SAT_VERSIONS,
    get_mock_config_map
)


class TestGetK8sAPI(unittest.TestCase):
    """Tests for ProductCatalog.get_k8s_api()."""

    def setUp(self):
        """Set up mocks."""
        self.mock_load_k8s = patch('cray_product_catalog.query.load_k8s').start()
        self.mock_corev1api = patch('cray_product_catalog.query.CoreV1Api').start()

    def tearDown(self):
        """Stop patches."""
        patch.stopall()

    def test_get_k8s_api(self):
        """Test the successful case of get_k8s_api."""
        api = ProductCatalog._get_k8s_api()
        self.mock_load_k8s.assert_called_once_with()
        self.mock_corev1api.assert_called_once_with()
        self.assertEqual(api, self.mock_corev1api.return_value)

    def test_get_k8s_api_config_exception(self):
        """Test when configuration can't be loaded."""
        self.mock_load_k8s.side_effect = ConfigException
        with self.assertRaises(ProductCatalogError):
            ProductCatalog._get_k8s_api()
        self.mock_load_k8s.assert_called_once_with()
        self.mock_corev1api.assert_not_called()


class TestProductCatalog(unittest.TestCase):
    """Tests for the ProductCatalog class."""

    def setUp(self):
        """Set up mocks."""
        self.mock_k8s_api = patch.object(ProductCatalog, '_get_k8s_api').start().return_value
        # Set up the mock K8s API to return a list of labeled ConfigMaps when we call
        # list_namespaced_config_map with the label selector for the product catalog.
        self.mock_k8s_api.list_namespaced_config_map.return_value = MOCK_LABELED_PRODUCT_CATALOG_CONFIG_MAPS
        # Set up the mock K8s API to return the main product catalog ConfigMap when we call
        # read_namespaced_config_map with the product catalog name and namespace. Note that
        # this should not be used unless the list_namespaced_config_map returns a V1ConfigMapList
        # with an empty list of items.
        self.mock_k8s_api.read_namespaced_config_map.return_value = MOCK_MAIN_PRODUCT_CATALOG_CONFIG_MAP

    def tearDown(self):
        """Stop patches."""
        patch.stopall()

    def create_and_assert_product_catalog(self):
        """Assert the product catalog was created as expected."""
        product_catalog = ProductCatalog(PRODUCT_CATALOG_CONFIG_MAP_NAME, MOCK_NAMESPACE)
        self.mock_k8s_api.list_namespaced_config_map.assert_called_once_with(
            MOCK_NAMESPACE, label_selector=PRODUCT_CATALOG_CONFIG_MAP_LABEL_STR
        )
        return product_catalog

    @staticmethod
    def get_invalid_yaml_config_map(product_name, config_map_name):
        """Create a mock ConfigMap with invalid YAML data."""
        metadata = Mock(spec=V1ObjectMeta)
        metadata.name = config_map_name
        return Mock(spec=V1ConfigMap, data={product_name: 'foo: bar: baz'}, metadata=metadata)

    def assert_product_catalog_data_matches(self, product_catalog):
        """Assert that the product catalog data matches the expected data.

        This compares the products in the given product_catalog with the expected
        data from combining the main ConfigMap data with the product-specific
        ConfigMap data.
        """
        product_combined_data = {
            'sat': SAT_VERSIONS,
            'cos': COS_VERSIONS,
            'cpe': CPE_VERSION,
            'other_product': OTHER_PRODUCT_VERSION
        }
        for product_name, product_data in product_combined_data.items():
            for version, version_data in product_data.items():
                self.assertEqual(version_data,
                                 product_catalog.get_product(product_name, version).data)

    def test_create_product_catalog(self):
        """Test creating a simple ProductCatalog."""
        product_catalog = self.create_and_assert_product_catalog()
        expected_names_and_versions = [
            (name, version) for name in ('sat', 'cos') for version in ('2.0.0', '2.0.1')
        ] + [('cpe', '2.0.0'), ('other_product', '2.0.0')]
        actual_names_and_versions = [
            (product.name, product.version) for product in product_catalog.products
        ]
        self.assertEqual(expected_names_and_versions, actual_names_and_versions)
        self.assert_product_catalog_data_matches(product_catalog)

    def test_create_product_catalog_labeled_invalid_product_data(self):
        """Test creating a ProductCatalog when a labeled ConfigMap contains invalid YAML."""
        invalid_product_name = 'invalid_product'
        self.mock_k8s_api.list_namespaced_config_map.return_value = Mock(
            items=[self.get_invalid_yaml_config_map(invalid_product_name,
                                                    f'cray-product-catalog-{invalid_product_name}')],
            spec=V1ConfigMapList
        )
        err_regex = (f'Failed to load data for product "{invalid_product_name}" from '
                     f'ConfigMap cray-product-catalog-{invalid_product_name}')
        with self.assertRaisesRegex(ProductCatalogError, err_regex):
            self.create_and_assert_product_catalog()

    def test_create_product_catalog_no_labeled_config_maps(self):
        """Test creating a ProductCatalog no labeled ConfigMaps are found but the main ConfigMap is present."""
        self.mock_k8s_api.list_namespaced_config_map.return_value = MOCK_EMPTY_LABELED_PRODUCT_CATALOG_CONFIG_MAPS
        self.mock_k8s_api.read_namespaced_config_map.return_value = MOCK_COMBINED_PRODUCT_CATALOG_CONFIG_MAP
        with self.assertLogs(level=logging.INFO) as logs_cm:
            product_catalog = self.create_and_assert_product_catalog()
        self.mock_k8s_api.read_namespaced_config_map.assert_called_once_with(
            PRODUCT_CATALOG_CONFIG_MAP_NAME, MOCK_NAMESPACE
        )
        self.assert_product_catalog_data_matches(product_catalog)
        self.assertEqual(logs_cm.records[0].levelname, 'INFO')
        self.assertRegex(logs_cm.records[0].message, 'No ConfigMaps found with label .* Falling back on ConfigMap')

    def test_create_product_catalog_no_labeled_config_maps_main_invalid(self):
        """Test creating a ProductCatalog when no labeled ConfigMaps exist, and the main ConfigMap has invalid YAML"""
        self.mock_k8s_api.list_namespaced_config_map.return_value = MOCK_EMPTY_LABELED_PRODUCT_CATALOG_CONFIG_MAPS
        self.mock_k8s_api.read_namespaced_config_map.return_value = self.get_invalid_yaml_config_map(
            'sat', 'cray-product-catalog'
        )
        err_regex = 'Failed to load data for product "sat" from ConfigMap cray-product-catalog'
        with self.assertRaisesRegex(ProductCatalogError, err_regex):
            self.create_and_assert_product_catalog()
        self.mock_k8s_api.read_namespaced_config_map.assert_called_once_with(
            PRODUCT_CATALOG_CONFIG_MAP_NAME, MOCK_NAMESPACE
        )

    def test_create_product_catalog_no_config_map_data(self):
        """Test creating a ProductCatalog when no labeled ConfigMaps exist, and the main ConfigMap has no data"""
        self.mock_k8s_api.list_namespaced_config_map.return_value = MOCK_EMPTY_LABELED_PRODUCT_CATALOG_CONFIG_MAPS
        self.mock_k8s_api.read_namespaced_config_map.return_value = Mock(data=None)
        err_regex = f'No data found in {MOCK_NAMESPACE}/{PRODUCT_CATALOG_CONFIG_MAP_NAME} ConfigMap.'
        with self.assertRaisesRegex(ProductCatalogError, err_regex):
            self.create_and_assert_product_catalog()
        self.mock_k8s_api.read_namespaced_config_map.assert_called_once_with(
            PRODUCT_CATALOG_CONFIG_MAP_NAME, MOCK_NAMESPACE
        )

    def assert_invalid_product_schema(self, product_name, invalid_versions):
        """Assert entry for given product name and version(s) does not match schema

        Args:
            product_name (str): The name of the product to check
            invalid_versions (str or list): The version(s) of the product to check
        """
        if isinstance(invalid_versions, str):
            invalid_versions = [invalid_versions]

        self.mock_k8s_api.list_namespaced_config_map.return_value = Mock(
            items=[Mock(data={product_name: safe_dump(MOCK_INVALID_PRODUCT_DATA.get(product_name))})],
            spec=V1ConfigMapList
        )
        with self.assertLogs(level=logging.WARNING) as logs_cm:
            product_catalog = self.create_and_assert_product_catalog()

        self.assertEqual(1, len(logs_cm.records))
        expected_error = ('The following products have product catalog data that '
                          'is not valid against the expected schema: ' +
                          ' '.join(f'{product_name}-{ver}' for ver in invalid_versions))

        self.assertEqual(logs_cm.records[0].levelname, 'WARNING')
        self.assertEqual(expected_error, logs_cm.records[0].message)
        self.assertEqual(product_catalog.products, [])

    def test_create_product_catalog_invalid_product_schema_for_docker(self):
        """
        Test creating a ProductCatalog when an entry contains valid YAML but does not match schema.
        As per schema, 'docker' should be an array.
        """
        self.assert_invalid_product_schema('sat', '2.1')

    def test_create_product_catalog_invalid_product_schema_for_s3(self):
        """
        Test creating a ProductCatalog when an entry contains valid YAML but does not match schema.
        As per schema, 's3' should be an array.
        """
        self.assert_invalid_product_schema('cpe', '2.1')

    def test_create_product_catalog_invalid_product_schema_for_manifests(self):
        """
        Test creating a ProductCatalog when an entry contains valid YAML but does not match schema.
        As per schema, 'manifests' should be an array.
        """
        self.assert_invalid_product_schema('cos', '2.1')

    def test_create_product_catalog_shallow(self):
        """Test creating a ProductCatalog with shallow=True"""
        product_catalog = ProductCatalog(PRODUCT_CATALOG_CONFIG_MAP_NAME, MOCK_NAMESPACE, shallow=True)
        self.mock_k8s_api.list_namespaced_config_map.assert_called_once_with(
            MOCK_NAMESPACE, label_selector=PRODUCT_CATALOG_CONFIG_MAP_LABEL_STR
        )

        # Assert that products were loaded (2 SAT versions, 2 COS versions, 1 CPE version, 1 other_product version)
        self.assertEqual(len(product_catalog.products), 6)

        # Assert that component_versions data is not present for each product
        for product in product_catalog.products:
            with self.assertLogs(level=logging.WARNING) as logs_cm:
                # Every property that looks at component_versions should be empty
                self.assertEqual({}, product.component_data)
                self.assertEqual([], product.docker_images)
                self.assertEqual([], product.helm_charts)
                self.assertEqual([], product.s3_artifacts)
                self.assertEqual([], product.loftsman_manifests)
                self.assertEqual([], product.repositories)
                self.assertEqual([], product.hosted_repositories)
                self.assertEqual([], product.group_repositories)
                self.assertEqual(set(), product.hosted_and_member_repo_names)

            # A warning is logged every time product.component_data is accessed. Each property accesses
            # "component_data" once, except hosted_and_member_repo_names, which accesses it twice.
            self.assertEqual(10, len(logs_cm.records))
            for log_record in logs_cm.records:
                self.assertEqual(log_record.levelname, 'WARNING')
                self.assertEqual('Data from "component_versions" may be incomplete due to shallow loading.',
                                 log_record.message)

        # Assert that the properties that are not based on component_versions data
        # are still populated. Just check the latest COS version, which has all this data.
        latest_cos = product_catalog.get_product('cos')
        self.assertNotEqual({}, latest_cos.configuration)
        self.assertIn('cos-config-management.git', latest_cos.clone_url)
        self.assertIsNotNone(latest_cos.commit)
        self.assertIsNotNone(latest_cos.import_branch)
        self.assertEqual(1, len(latest_cos.recipes))
        self.assertEqual(1, len(latest_cos.images))

    def test_create_product_catalog_extra_product_version(self):
        """Test creating a ProductCatalog with an extra product version in a product-specific ConfigMap"""
        # Add an extra SAT version to the separate SAT ConfigMap data
        extra_sat_version = '9.9.9'
        sat_separate_cm_data = copy.deepcopy(SAT_SEPARATE_CM_DATA)
        sat_separate_cm_data[extra_sat_version] = copy.deepcopy(SAT_SEPARATE_CM_DATA['2.0.1'])
        mock_config_map_list = Mock(
            spec=V1ConfigMapList,
            items=[
                get_mock_config_map(PRODUCT_CATALOG_CONFIG_MAP_NAME, MOCK_MAIN_PRODUCT_CATALOG_DATA),
                get_mock_config_map('cray-product-catalog-sat', {'sat': safe_dump(sat_separate_cm_data)})
            ]
        )
        self.mock_k8s_api.list_namespaced_config_map.return_value = mock_config_map_list

        product_catalog = self.create_and_assert_product_catalog()
        product_catalog.get_product('sat', extra_sat_version)  # Should not raise an error

        # If loaded with shallow=True, the extra version should not be present
        shallow_product_catalog = ProductCatalog(PRODUCT_CATALOG_CONFIG_MAP_NAME, MOCK_NAMESPACE, shallow=True)
        err_regex = f'No installed products with name sat and version {extra_sat_version}'
        with self.assertRaisesRegex(ProductCatalogError, err_regex):
            shallow_product_catalog.get_product('sat', extra_sat_version)

    def test_get_matching_product(self):
        """Test getting a particular product by name/version."""
        product_catalog = self.create_and_assert_product_catalog()
        expected_matching_name_and_version = ('cos', '2.0.0')
        actual_matching_product = product_catalog.get_product('cos', '2.0.0')
        self.assertEqual(
            expected_matching_name_and_version, (actual_matching_product.name, actual_matching_product.version)
        )
        expected_component_data = COS_VERSIONS['2.0.0']
        self.assertEqual(expected_component_data, actual_matching_product.data)

    def test_get_latest_matching_product(self):
        """Test getting the latest version of a product"""
        product_catalog = self.create_and_assert_product_catalog()
        expected_matching_name_and_version = ('sat', '2.0.1')
        actual_matching_product = product_catalog.get_product('sat')
        self.assertEqual(expected_matching_name_and_version,
                         (actual_matching_product.name, actual_matching_product.version))
        expected_component_data = SAT_VERSIONS['2.0.1']
        self.assertEqual(expected_component_data, actual_matching_product.data)

    def test_get_non_existent_product_latest(self):
        """Test getting the latest version of a product that does not exist."""
        product_name = 'non_existent_product'
        product_catalog = self.create_and_assert_product_catalog()
        err_regex = f'No installed products with name {product_name}'
        with self.assertRaisesRegex(ProductCatalogError, err_regex):
            product_catalog.get_product(product_name)

    def test_get_non_existent_product_name(self):
        """Test getting a product whose name does not exist in the product catalog."""
        product_name = 'non_existent_product'
        product_version = '1.0.0'
        product_catalog = self.create_and_assert_product_catalog()
        err_regex = f'No installed products with name {product_name} and version {product_version}.'
        with self.assertRaisesRegex(ProductCatalogError, err_regex):
            product_catalog.get_product(product_name, product_version)

    def test_get_non_existent_product_version(self):
        """Test getting a non-existent version of a product in the product catalog."""
        product_name = 'sat'
        product_version = '999.999.999'
        product_catalog = self.create_and_assert_product_catalog()
        err_regex = f'No installed products with name {product_name} and version {product_version}.'
        with self.assertRaisesRegex(ProductCatalogError, err_regex):
            product_catalog.get_product(product_name, product_version)


class TestInstalledProductVersion(unittest.TestCase):
    """Tests for the InstalledProductVersion class."""
    def setUp(self):
        """Create an InstalledProductVersion object to test"""
        # Use this product version because its data is most complete
        self.installed_product_version = InstalledProductVersion(
            'cos', '2.0.1', COS_VERSIONS['2.0.1']
        )

    def tearDown(self):
        """Stop patches."""
        patch.stopall()

    def test_docker_images(self):
        """Test getting the Docker images."""
        expected_docker_image_versions = [('cray/cray-cos', '1.0.1'),
                                          ('cray/cos-cfs-install', '1.4.0')]
        self.assertEqual(
            expected_docker_image_versions, self.installed_product_version.docker_images
        )

    def test_no_docker_images(self):
        """Test a product that has an empty dictionary under the 'docker' key returns an empty list."""
        product_with_no_docker_images = InstalledProductVersion(
            'sat', '0.9.9', {'component_versions': {'docker': {}}}
        )
        self.assertEqual(product_with_no_docker_images.docker_images, [])

    def test_no_docker_images_null(self):
        """Test a product that has None under the 'docker' key returns an empty list."""
        product_with_no_docker_images = InstalledProductVersion(
            'sat', '0.9.9', {'component_versions': {'docker': None}}
        )
        self.assertEqual(product_with_no_docker_images.docker_images, [])

    def test_no_docker_images_empty_list(self):
        """Test a product that has an empty list under the 'docker' key returns an empty list."""
        product_with_no_docker_images = InstalledProductVersion(
            'sat', '0.9.9', {'component_versions': {'docker': []}}
        )
        self.assertEqual(product_with_no_docker_images.docker_images, [])

    def test_helm_charts(self):
        """Test getting the Helm charts."""
        expected_helm_charts_versions = [
            ('cos-config', '0.4.76'),
            ('cos-sle15sp3-artifacts', '1.3.23'),
            ('cray-cps', '1.8.15')
        ]
        self.assertEqual(
            expected_helm_charts_versions, self.installed_product_version.helm_charts
        )

    def test_no_helm_charts(self):
        """Test a product that has an empty dictionary under the 'helm' key returns an empty list."""
        product_with_no_helm_charts = InstalledProductVersion(
            'sat', '0.9.9', {'component_versions': {'helm': {}}}
        )
        self.assertEqual(product_with_no_helm_charts.helm_charts, [])

    def test_no_helm_charts_null(self):
        """Test a product that has None under the 'helm' key returns an empty list."""
        product_with_no_helm_charts = InstalledProductVersion(
            'sat', '0.9.9', {'component_versions': {'helm': None}}
        )
        self.assertEqual(product_with_no_helm_charts.helm_charts, [])

    def test_no_helm_charts_empty_list(self):
        """Test a product that has an empty list under the 'helm' key returns an empty list."""
        product_with_no_helm_charts = InstalledProductVersion(
            'sat', '0.9.9', {'component_versions': {'helm': []}}
        )
        self.assertEqual(product_with_no_helm_charts.helm_charts, [])

    def test_s3_artifacts(self):
        """Test getting the s3 artifacts."""
        expected_s3_artifacts = [('boot-images', 'PE/CPE-base.x86_64-2.0.squashfs'),
                                 ('boot-images', 'PE/CPE-amd.x86_64-2.0.squashfs')]
        product_with_s3_artifacts = InstalledProductVersion(
            'cpe', '2.0.0', CPE_VERSION['2.0.0']
        )
        self.assertEqual(expected_s3_artifacts, product_with_s3_artifacts.s3_artifacts)

    def test_no_s3_artifacts(self):
        """Test a product that has an empty dictionary under the 's3' key returns an empty list."""
        product_with_no_s3_artifacts = InstalledProductVersion(
            'sat', '0.9.9', {'component_versions': {'s3': {}}}
        )
        self.assertEqual(product_with_no_s3_artifacts.s3_artifacts, [])

    def test_no_s3_artifacts_null(self):
        """Test a product that has None under the 's3' key returns an empty list."""
        product_with_no_s3_artifacts = InstalledProductVersion(
            'sat', '0.9.9', {'component_versions': {'s3': None}}
        )
        self.assertEqual(product_with_no_s3_artifacts.s3_artifacts, [])

    def test_no_s3_artifacts_empty_list(self):
        """Test a product that has an empty list under the 's3' key returns an empty list."""
        product_with_no_s3_artifacts = InstalledProductVersion(
            'sat', '0.9.9', {'component_versions': {'s3': []}}
        )
        self.assertEqual(product_with_no_s3_artifacts.s3_artifacts, [])

    def test_loftsman_manifests(self):
        """Test getting the Loftsman manifests."""
        expected_loftsman_manifests = ['config-data/argo/loftsman/cos/2.0.0/manifests/cos-services.yaml']
        product_with_loftsman_manifests = InstalledProductVersion(
            'cos', '2.0.0', COS_VERSIONS['2.0.0']
        )
        self.assertEqual(expected_loftsman_manifests, product_with_loftsman_manifests.loftsman_manifests)

    def test_no_loftsman_manifests_empty_list(self):
        """Test a product that has an empty list under the 'manifests' key returns an empty list."""
        product_with_no_loftsman_manifests = InstalledProductVersion(
            'sat', '0.9.9', {'component_versions': {'manifests': []}}
        )
        self.assertEqual(product_with_no_loftsman_manifests.loftsman_manifests, [])

    def test_str(self):
        """Test the string representation of InstalledProductVersion."""
        expected_str = 'cos-2.0.1'
        self.assertEqual(
            expected_str, str(self.installed_product_version)
        )

    def test_group_repos(self):
        """Test getting group repo data for an InstalledProductVersion."""
        expected_group_repos = [{'members': ['cos-2.0.1-sle-15sp2'], 'name': 'cos-sle-15sp2', 'type': 'group'}]
        self.assertEqual(
            expected_group_repos, self.installed_product_version.group_repositories
        )

    def test_hosted_repos(self):
        """Test getting hosted repo names for an InstalledProductVersion."""
        expected_hosted_repo_names = {'cos-2.0.1-sle-15sp2'}
        self.assertEqual(
            expected_hosted_repo_names, self.installed_product_version.hosted_and_member_repo_names
        )

    def test_hosted_repos_without_members(self):
        """Test getting hosted repo names that are listed only as hosted repos but not a member of a group."""
        sat_version_data = copy.deepcopy(SAT_VERSIONS['2.0.0'])
        sat_version_data['component_versions']['repositories'] = [
            {'name': 'my-hosted-repo', 'type': 'hosted'}
        ]
        ipv = InstalledProductVersion('sat', '2.0.0', sat_version_data)
        expected_hosted_repo_names = {'my-hosted-repo'}
        self.assertEqual(ipv.hosted_and_member_repo_names, expected_hosted_repo_names)

    def test_hosted_repos_only_members(self):
        """Test getting hosted repo names that are not listed except as a member of a group."""
        sat_version_data = copy.deepcopy(SAT_VERSIONS['2.0.0'])
        sat_version_data['component_versions']['repositories'] = [
            {'name': 'my-group-repo', 'type': 'group', 'members': ['my-hosted-repo']}
        ]
        ipv = InstalledProductVersion('sat', '2.0.0', sat_version_data)
        expected_hosted_repo_names = {'my-hosted-repo'}
        self.assertEqual(ipv.hosted_and_member_repo_names, expected_hosted_repo_names)

    def test_configuration_items_present(self):
        """Test getting configuration values when the product includes them."""
        attr_and_expected_val = [
            ('clone_url', 'https://vcs.machine.dev.cray.com/vcs/cray/cos-config-management.git'),
            ('commit', 'f0b17e13fcf7dd3b896196776e4547fdb98f1da7'),
            ('import_branch', 'cray/cos/2.0.1')
        ]
        for attr, expected_val in attr_and_expected_val:
            with self.subTest(attr=attr):
                self.assertEqual(expected_val, getattr(self.installed_product_version, attr))

    def test_configuration_items_missing(self):
        """Test getting configuration values when the product does not include them in its configuration data."""
        attrs = ['clone_url', 'commit', 'import_branch']
        for attr in attrs:
            with self.subTest(attr=attr):
                cos_version_data = copy.deepcopy(COS_VERSIONS['2.0.1'])
                del cos_version_data['configuration'][attr]
                ipv = InstalledProductVersion('cos', '2.0.1', cos_version_data)
                self.assertIsNone(getattr(ipv, attr))

    def test_configuration_missing(self):
        """Test getting configuration values when the product does not include any configuration data."""
        attrs = ['clone_url', 'commit', 'import_branch']
        cos_version_data = copy.deepcopy(COS_VERSIONS['2.0.1'])
        del cos_version_data['configuration']
        ipv = InstalledProductVersion('cos', '2.0.1', cos_version_data)
        for attr in attrs:
            with self.subTest(attr=attr):
                self.assertIsNone(getattr(ipv, attr))

    def test_recipes(self):
        """Test getting recipes when the product has one."""
        expected_recipes = [{'name': 'cray-shasta-compute-sles15sp2.x86_64-1.5.66',
                             'id': '54bc9447-73ba-4b06-a647-e5225451596d'}]
        self.assertEqual(expected_recipes, self.installed_product_version.recipes)

    def test_images(self):
        """Test getting images when the product has one."""
        expected_images = [{'name': 'cray-shasta-compute-sles15sp2.x86_64-1.5.66',
                            'id': 'e2d58d7e-42b7-434d-b689-31ca3d053c51'}]
        self.assertEqual(expected_images, self.installed_product_version.images)

    def test_ims_resources_missing(self):
        """Test getting recipes/images when the product has no corresponding key in its data."""
        ipv = InstalledProductVersion('sat', '2.0.0', SAT_VERSIONS['2.0.0'])
        for attr in ['recipes', 'images']:
            with self.subTest(attr=attr):
                self.assertEqual([], getattr(ipv, attr))

    def test_ims_resources_null(self):
        """Test getting recipes/images when the product has a null value for the corresponding key."""
        for attr in ['recipes', 'images']:
            sat_version_data = copy.deepcopy(SAT_VERSIONS['2.0.0'])
            sat_version_data[attr] = None
            ipv = InstalledProductVersion('sat', '2.0.0', sat_version_data)
            with self.subTest(attr=attr):
                self.assertEqual([], getattr(ipv, attr))

    def test_ims_resources_empty(self):
        """Test getting recipes/images when the product has an empty dict value for the corresponding key."""
        for attr in ['recipes', 'images']:
            sat_version_data = copy.deepcopy(SAT_VERSIONS['2.0.0'])
            sat_version_data[attr] = {}
            ipv = InstalledProductVersion('sat', '2.0.0', sat_version_data)
            with self.subTest(attr=attr):
                self.assertEqual([], getattr(ipv, attr))

    def test_active_true(self):
        """Test active when 'active' key is present and True"""
        cos_version_data = copy.deepcopy(COS_VERSIONS['2.0.1'])
        cos_version_data['active'] = True
        ipv = InstalledProductVersion('cos', '2.0.1', cos_version_data)
        self.assertTrue(ipv.active)

    def test_active_false(self):
        """Test active when 'active' key is present and True"""
        cos_version_data = copy.deepcopy(COS_VERSIONS['2.0.1'])
        cos_version_data['active'] = False
        ipv = InstalledProductVersion('cos', '2.0.1', cos_version_data)
        self.assertFalse(ipv.active)

    def test_active_key_missing(self):
        """Test active when 'active' key is present and True"""
        self.assertFalse(self.installed_product_version.active)

    def test_active_supported_key_missing(self):
        """Test active_supported when 'active' key is missing"""
        self.assertFalse(self.installed_product_version.supports_active)

    def test_active_supported_key_present(self):
        """Test active_supported when 'active' key is present"""
        cos_version_data = copy.deepcopy(COS_VERSIONS['2.0.1'])
        cos_version_data['active'] = True
        ipv = InstalledProductVersion('cos', '2.0.1', cos_version_data)
        self.assertTrue(ipv.supports_active)


if __name__ == '__main__':
    unittest.main()
