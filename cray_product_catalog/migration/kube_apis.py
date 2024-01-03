#
# MIT License
#
# (C) Copyright 2023-2024 Hewlett Packard Enterprise Development LP
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
Kubernets API
"""

import logging
from kubernetes import client
from kubernetes.client.rest import ApiException
from kubernetes.client.api_client import ApiClient
from kubernetes.client.models.v1_config_map import V1ConfigMap
from kubernetes.client.models.v1_object_meta import V1ObjectMeta
from urllib3.util.retry import Retry
from urllib3.exceptions import MaxRetryError
from cray_product_catalog.logging import configure_logging
from cray_product_catalog.util.k8s import load_k8s
from . import retry_count


class KubernetesApi:
    """Class for wrapping Kubernetes API"""
    def __init__(self):
        configure_logging()
        self.logger = logging.getLogger(__name__)
        load_k8s()

        retry = Retry(
            total=retry_count, read=retry_count, connect=retry_count, backoff_factor=0.3,
            status_forcelist=(500, 502, 503, 504)
        )
        self.kclient = ApiClient()
        self.kclient.rest_client.pool_manager.connection_pool_kw['retries'] = retry
        self.api_instance = client.CoreV1Api(self.kclient)

    def create_config_map(self, name, namespace, data, label):
        """Creates ConfigMap
        :param dict data: Content of ConfigMap
        :param str name: ConfigMap name to be created
        :param str namespace: Namespace in which ConfigMap has to be created
        :param dict label: Label with which ConfigMap has to be created
        :return: bool
        """
        try:
            cm_body = V1ConfigMap(
                metadata=V1ObjectMeta(
                    name=name,
                    labels=label
                ),
                data=data
            )
            self.api_instance.create_namespaced_config_map(
                namespace=namespace, body=cm_body
            )
            return True
        except MaxRetryError as err:
            self.logger.exception('MaxRetryError: %s', err)
            return False
        except ApiException as err:
            # The full string representation of ApiException is very long, so just log err.reason.
            self.logger.exception('ApiException: %s', err.reason)
            return False
        self.logger.error('Unknown error creating ConfigMap')
        return False
        self.logger.error('Unknown error creating ConfigMap')
        return False

    def list_config_map(self, namespace, label):
        """ Reads all the ConfigMaps with certain label in particular namespace
        :param str namespace: Value of namespace from where ConfigMap has to be listed
        :param str label: String format of label "type=xyz"
        :return: V1ConfigMapList
                 If there is any error, returns None
        """
        if not all((label, namespace)):
            self.logger.info("Either label or namespace is empty, not reading ConfigMap.")
            return None
        try:
            return self.api_instance.list_namespaced_config_map(namespace, label_selector=label).items
        except MaxRetryError as err:
            self.logger.exception('MaxRetryError: %s', err)
            return None
        except ApiException as err:
            # The full string representation of ApiException is very long, so just log err.reason.
            self.logger.exception('ApiException: %s', err.reason)
            return None
        self.logger.error('Unknown error listing ConfigMaps')
        return None
        self.logger.error('Unknown error listing ConfigMaps')
        return None

    def list_config_map_names(self, namespace, label):
        """ Reads all the ConfigMaps with certain label in particular namespace
        :param str namespace: Value of namespace from where ConfigMap has to be listed
        :param str label: String format of label "type=xyz"
        :return: [str]
        """
        cm_output = self.list_config_map(namespace, label)

        list_cm_names = []

        if not cm_output:
            return list_cm_names

        # parse the output to get only names
        for cm in cm_output:
            try:
                list_cm_names.append(cm.metadata.name)
            except Exception:
                continue

        return list_cm_names

    def read_config_map(self, name, namespace):
        """Reads ConfigMap based on provided name and namespace
        :param Str name: Name of ConfigMap to read
        :param Str namespace: Namespace from which ConfigMap has to be read
        :return: V1ConfigMap
                 Returns None in case of any error
        """
        # Check if both values are not empty
        if not all((name, namespace)):
            self.logger.exception("Either name or namespace is empty, not reading ConfigMap.")
            return None
        try:
            return self.api_instance.read_namespaced_config_map(name, namespace)
        except MaxRetryError as err:
            self.logger.exception('MaxRetryError: %s', err)
            return None
        except ApiException as err:
            # The full string representation of ApiException is very long, so just log err.reason.
            self.logger.exception('ApiException: %s', err.reason)
            return None
        self.logger.error('Unknown error reading ConfigMap')
        return None
        self.logger.error('Unknown error reading ConfigMap')
        return None

    def delete_config_map(self, name, namespace):
        """Delete the ConfigMap
        :param Str name: Name of ConfigMap to be deleted
        :param Str namespace: Namespace from which ConfigMap has to be deleted
        :return: bool; If success True else False
        """
        try:
            self.api_instance.delete_namespaced_config_map(name, namespace)
            return True
        except MaxRetryError as err:
            self.logger.exception('MaxRetryError: %s', err)
            return False
        except ApiException as err:
            # The full string representation of ApiException is very long, so just log err.reason.
            self.logger.exception('ApiException: %s', err.reason)
            return False
        self.logger.error('Unknown error deleting ConfigMap')
        return False
