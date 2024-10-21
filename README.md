# Cray Product Catalog

This repository contains the Python source code and YAML schema files for the Cray
Product Catalog. The associated Docker image and Helm chart are created from the
[`cray-product-catalog`](https://github.com/Cray-HPE/cray-product-catalog) repository.

See the [CSM Compatibility Matrix](https://github.com/Cray-HPE/cray-product-catalog/wiki/CSM-Compatibility-Matrix)
for more information about what version of the Cray Product Catalog Update image to
use in your product.

At minimum, the `catalog_update.py` script takes environment variables `PRODUCT`
and `PRODUCT_VERSION` and applies the content of a file denoted by
`YAML_CONTENT_FILE` file as follows:

```yaml
{PRODUCT}:
  {PRODUCT_VERSION}:
    {content of yaml file (in YAML_CONTENT_FILE)}
```

For backwards compatibility, the environment variable `YAML_CONTENT` is
equivalent to `YAML_CONTENT_FILE`. As an alternative to `YAML_CONTENT_FILE`,
a YAML-formatted string may be passed using the environment variable
`YAML_CONTENT_STRING`.

The product catalog is a lightweight software inventory of sorts, and allows for
system users to view a product and its associated versions and version metadata
that have been _installed_ on the system.

The cray-product-catalog-update image is assumed to be running in the CSM
Kubernetes cluster by an actor that has permissions to read and update config
maps in the namespace that is configured.

## Getting Started

The main use case for cray-product-catalog is for a product to add install-time
information and metadata to the cray-product-catalog config map located in the
services namespace via a Kubernetes job as part of a Helm chart. The image
could also be used via podman on an NCN, but this has not been tested.

NOTE: As of 2.3.0 version of cray-product-catalog, the configmap for cray-product-catalog
has been split into multiple configmaps in the services namespace. The main configmap is
referred to as cray-product-catalog, and the product-specific configmap names have the format
cray-product-catalog-<product-name>.

The main cray-product-catalog configmap has entries for each product version. The
product-specific configmaps include detailed entries for each version of that product.

## Configuration

All configuration options are provided as environment variables.

### Required Environment Variables

* `PRODUCT` = (no default)

> The name of the Cray/Shasta product that is being cataloged.

* `PRODUCT_VERSION` = (no default)

> The SemVer version of the Cray/Shasta product that is being imported, e.g.
  `1.2.3`.

* One of:

    * `YAML_CONTENT_FILE` = (no default)

      > The filesystem location of the YAML that will be added to the config map.

    * `YAML_CONTENT` = (no default)

      > Equivalent to `YAML_CONTENT_FILE`, included for backwards compatibility.

    * `YAML_CONTENT_STRING` = (no default)

      > A YAML-formatted string to be used as an alternative to `YAML_CONTENT_FILE`.

### Optional Environment Variables

 * `CONFIG_MAP` = `cray-product-catalog`

 > The name of the config map to add the `YAML_CONTENT_FILE` to.

 * `CONFIG_MAP_NAMESPACE` = `services`

 > The Kubernetes namespace of the `CONFIG_MAP`.

 * `SET_ACTIVE_VERSION` = `''`

 > When set, the given product-version will have a field called 'active' set to `true`. Other
 > versions of the product will automatically have the field set to `false.` Cannot be used with
 > `REMOVE_ACTIVE_FIELD` (see below).

 * `REMOVE_ACTIVE_FIELD` = `''`

 > When set, all versions of the given product will have the 'active' field removed from the
 > ConfigMap data. Cannot be used with `SET_ACTIVE_VERSION` (see above).

 * `UPDATE_OVERWRITE` = `''`

> When set, the catalog_update function will perform an update that will
> overwrite the entire product data in the configmap. Contrasted to the default implementation
> which will perform a merge operation between the two maps.
> This is useful for removing nested data or just simply removing entire
> entries from the config map.

## Versioning and Releases

Versions are calculated automatically using `gitversion`. The full SemVer
output is governed by the `GitVersion.yml` file in the root of this repo.

Run `gitversion -output json` to see the current version based on the checked
out commit.

## Contributing

This repo uses [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
and the [CSM Gitflow Development Process]( https://github.com/Cray-HPE/community/wiki/Gitflow-Development-Process).

CMS-core-product-support team members should make a branch. Others, make a fork.

## Built With

* Python 3
* Kubernetes Python Client
* [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
* [Gitversion](https://gitversion.net)
* Good intentions

## Changelog

See the [CHANGELOG](CHANGELOG.md) for changes. This file uses the [Keep A Changelog](https://keepachangelog.com)
format.

## Copyright and License

This project is copyrighted by Hewlett Packard Enterprise Development LP and is under the MIT
license. See the [LICENSE](LICENSE) file for details.
