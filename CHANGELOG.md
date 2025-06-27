# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Dependencies

- Bump `dangoslen/dependabot-changelog-helper` from 3 to 4 ([#22](https://github.com/Cray-HPE/cray-product-catalog-core/pull/22))
- Update `kubernetes` version to match CSM 1.7

## [2.6.0] - 2024-11-12

### Added

- CASMCMS-9199: Added support for Python 3.6

## [2.5.0] - 2024-10-21

### Changed

- CASMTRIAGE-7413: Split this repository off from the `cray-product-catalog` repository, to separate
  the product catalog source code from the Docker image and Helm chart. The original repository will
  be used to build and publish those. This repository contains the product catalog source code and schemas.

> Versions below this point were published from the cray-product-catalog repository, before that
> repository was split into two. The commit history was copied into this repository, but the tags
> will not exist here.

## [2.4.1] - 2024-09-19

### Changed
- CASMCMS-9142: Install Python modules using `--user` to prevent build failures, and build inside Docker container

## [2.4.0] - 2024-09-09

### Dependencies
- CSM 1.6 moved to Kubernetes 1.24, so use client v24.x to ensure compatibility
- Bump `tj-actions/changed-files` from 44 to 45 ([#349](https://github.com/Cray-HPE/cray-product-catalog/pull/349))
- CASMCMS-9132 - updated to 'docker-kubectl' image version 1.24.17 for the Kubernetes 1.24 upgrade.

## [2.3.1] - 2024-08-15

### Changed
- CASMCMS-9098: Restore `install_requires` and `long_description` to Python module by creating [`MANIFEST.in`](MANIFEST.in)
- CASM-4815 : Updating the README to include information on migration of cray-product-catalog configmap.
- List installed Python packages in Dockerfile, for build logging purposes
- Pin major and minor versions of Python dependencies, but use latest patch version

## [2.3.0] - 2024-07-16

### Changed
- CASM-4731: change to adapt cray-product-catalog to include empty dictionary objects [`config_map_data_handler.py`](cray_product_catalog/migration/config_map_data_handler.py)
- CASM-4741: give a warning instead of raising exception if product configmap is not present [`catalog_update.py`](cray_product_catalog/catalog_delete.py)
- CASM-4743: add check if the configmap has already been migrated before attempting to migrate [`main.py`](cray_product_catalog/migration/main.py)

### Dependencies
- Bump `urllib3` from 1.26.18 to 1.26.19 ([#324](https://github.com/Cray-HPE/cray-product-catalog/pull/324))

## [2.2.0] - 2024-05-29

### Changed
- CASMCMS-9012: Modify build process to remove dependencies on additional files from `setup.py`. This should allow installs from the
  Python module source files to work.

### Dependencies
- Bump `tj-actions/changed-files` from 43 to 44 ([#320](https://github.com/Cray-HPE/cray-product-catalog/pull/320))
- Require Python 3.9

## [2.1.0] - 2024-03-20

### Changed
- CASMTRIAGE-6794: Improved logging in [`catalog_update.py`](cray_product_catalog/catalog_update.py),
  including changing logging which caused IUF to incorrectly think the catalog update failed.

### Dependencies
- Bump `cachetools` from 5.3.2 to 5.3.3 ([#315](https://github.com/Cray-HPE/cray-product-catalog/pull/315))
- Bump `tj-actions/changed-files` from 42 to 43 ([#316](https://github.com/Cray-HPE/cray-product-catalog/pull/316))

## [2.0.1] - 2024-02-22

### Dependencies
- Regress `kubernetes` from 26.1.0 to 22.6.0 to match CSM 1.6 Kubernetes version

## [2.0.0] - 2024-02-08

### Changed

- CASM-4350: To address the 1MiB size limit of Kubernetes ConfigMaps, the 
  `cray-product-catalog` Kubernetes ConfigMap is split into multiple smaller
  ConfigMaps with each product's `component_versions` data in its own ConfigMap.
  Modified `create`, `modify`, `delete` and `query` feature to support
  the split of single ConfigMap into multiple ConfigMaps.
- Added new argument `max_attempts` to `modify_config_map` function in
  [`catalog_delete.py`](cray_product_catalog/catalog_delete.py), because we need not retry 100
  times when read ConfigMap fails for a product ConfigMap.
- CASM-4504: Added label "type=cray-product-catalog" to all cray-product-catalog related ConfigMaps
- Implemented migration of cray-product-catalog ConfigMap to multiple ConfigMaps as part of pre-upgrade steps
- Added migration job to the configmap-hook

### Dependencies
- Bump `tj-actions/changed-files` from 40 to 42 ([#307](https://github.com/Cray-HPE/cray-product-catalog/pull/307), [#309](https://github.com/Cray-HPE/cray-product-catalog/pull/309))

## [1.10.0] - 2023-11-29

### Dependencies
- Bump `websocket-client` from 1.6.1 to 1.6.4 ([#283](https://github.com/Cray-HPE/cray-product-catalog/pull/283), [#293](https://github.com/Cray-HPE/cray-product-catalog/pull/293), [#299](https://github.com/Cray-HPE/cray-product-catalog/pull/299))
- Bump `tj-actions/changed-files` from 37 to 40 ([#284](https://github.com/Cray-HPE/cray-product-catalog/pull/284), [#287](https://github.com/Cray-HPE/cray-product-catalog/pull/287), [#302](https://github.com/Cray-HPE/cray-product-catalog/pull/302))
- Bump `actions/checkout` from 3 to 4 ([#288](https://github.com/Cray-HPE/cray-product-catalog/pull/288))
- Bump `urllib3` from 1.26.16 to 1.26.18 ([#296](https://github.com/Cray-HPE/cray-product-catalog/pull/296), [#300](https://github.com/Cray-HPE/cray-product-catalog/pull/300))
- Bump `stefanzweifel/git-auto-commit-action` from 4 to 5 ([#298](https://github.com/Cray-HPE/cray-product-catalog/pull/298))
- Bump `cachetools` from 5.3.1 to 5.3.2 ([#301](https://github.com/Cray-HPE/cray-product-catalog/pull/301))
- Bump `pyasn1` from 0.5.0 to 0.5.1 ([#303](https://github.com/Cray-HPE/cray-product-catalog/pull/303))

## [1.9.0] - 2023-08-16

### Changed
- CASM-3981: Added S3 artifacts and Loftsman manifests to the Product Catalog schema
- CASM-3981: Added functions to retrieve Helm charts, S3 artifacts, and Loftsman manifests from the Product Catalog
- Disabled concurrent Jenkins builds on same branch/commit
- Added build timeout to avoid hung builds

### Dependencies
- Bump `jsonschema` from 4.18.3 to 4.18.6 (#270, [#275](https://github.com/Cray-HPE/cray-product-catalog/pull/275))
- Bump `pip` from 23.2 to 23.2.1 ([#274](https://github.com/Cray-HPE/cray-product-catalog/pull/274))

## [1.8.12] - 2023-07-18

### Dependencies
- Bump `google-auth` from 2.21.0 to 2.22.0 (#258)
- Bump `jsonschema` from 4.18.0 to 4.18.3 (#259, #262)
- Bump `PyYAML` from 6.0 to 6.0.1 (#264)
- Pin `pip` version to 23.2 (#264)
- Pin `setuptools` version to 68.0.0 (#264)
- Pin `wheel` version to 0.40.0 (#264)

## [1.8.11] - 2023-07-10

### Changed
- CASMCMS-8709: Linting of log messages and code comments to remove inconsistencies.
- CASMCMS-8709: Created `.pylintrc` configuration file for use when running pylint during builds.
- CASMCMS-8709: Made improvements based on pylint warnings and suggestions (no functional changes).

### Dependencies
- Bump `charset-normalizer` from 3.1.0 to 3.2.0 (#254)

## [1.8.10] - 2023-07-07

### Changed

- Update `pip` before installing packages in Dockerfile, to avoid image creation
  failure caused by `pip` building `maturin` from source. (#250)

### Dependencies

- Bump `urllib3` from 1.26.15 to 1.26.16
- Bump `jsonschema` from 4.17.3 to 4.18.0 (#250)

## [1.8.9] - 2023-07-05

### Added

- Added `UPDATE_OVERWRITE` environment variable to support cases where
  full control of the products configmap data is required.

### Changed

- dependabot: Bump `requests` from 2.30.0 to 2.31.0
- dependabot: Bump `google-auth` from 2.17.3 to 2.21.0
- dependabot: Bump `cachetools` from 5.3.0 to 5.3.1
- dependabot: Bump `websocket-client` from 1.5.2 to 1.6.1
- Added `UPDATE_OVERWRITE` environment variable to support cases where
  full control of the products configmap data is required.

## [1.8.8] - 2023-05-31

### Changed

- dependabot: Bump `websocket-client` from 1.5.1 to 1.5.2
- CASM-4224: Improve logging for [`catalog_update.py`](cray_product_catalog/catalog_update.py) for use with IUF.

## [1.8.7] - 2023-05-08

### Changed

- dependabot: Bump `pyasn1-modules` from 0.2.8 to 0.3.0
- dependabot: Bump `pyasn1` from 0.4.8 to 0.5.0
- dependabot: Bump `attrs` from 22.2.0 to 23.1.0
- dependabot: Bump `requests` from 2.28.2 to 2.30.0
- dependabot: Bump `certifi` from 2022.12.7 to 2023.5.7

## [1.8.6] - 2023-04-24

### Changed

- dependabot: Bump `jsonschema` from 4.4.0 to 4.17.3
- dependabot: Bump `kubernetes` from 23.3.0 to 26.1.0
- dependabot: Bump `certifi` from 2021.10.8 to 2022.12.7
- dependabot: Bump `oauthlib` from 3.2.0 to 3.2.2
- dependabot: Bump `rsa` from 4.8 to 4.9
- dependabot: Bump `idna` from 3.3 to 3.4
- dependabot: Bump `cachetools` from 5.0.0 to 5.3.0
- dependabot: Bump `google-auth` from 2.17.2 to 2.17.3

## [1.8.5] - 2023-04-11

### Changed

- dependabot: Bump `charset-normalizer` from 2.0.12 to 3.1.0.
- dependabot: Bump `attrs` from 21.4.0 to 22.2.0.
- dependabot: Bump `pyrsistent` from 0.18.1 to 0.19.3.
- dependabot: Bump `requests` from 2.27.1 to 2.28.2

## [1.8.4] - 2023-04-07

### Changed

- dependabot: Bump `google-auth` from 2.6.0 to 2.17.2
- dependabot: Bump `websocket-client` from 1.3.1 to 1.5.1
- dependabot: Bump `urllib3` from 1.26.8 to 1.26.15

## [1.8.3] - 2023-04-06

### Fixed

- Fixed bad image path in the helm chart

### Changed

- Updated chart maintainer
- Correct version strings used in Chart

## [1.8.2] - 2023-01-10

### Fixed

- Fixed an issue where inserting certain types of data would loop forever.

## [1.8.1] - 2022-12-20

### Added

- Add Artifactory authentication to Jenkinsfile

## [1.8.0] - 2022-12-20

### Added

- Added an environment variable `REMOVE_ACTIVE_FIELD`. When set, the `catalog_update`
  script will remove the 'active' field for all versions of the given product.

### Changed

- Modified github workflow for checking license text to use authenticated access to
  artifactory server hosting license-checker image.

- Changed format of log messages to be prefixed with severity.

### Fixed

- Fixed an issue where log messages from child modules were not being printed.

## [1.7.0] - 2022-11-17

### Changed

- Added a github workflow for checking license text separate from the organization-
  wide "license-check" workflow.

- Reverted github workflows regarding image building and publishing and 
  releases back to Jenkins pipelines.

- Renamed `YAML_CONTENT` environment variable to `YAML_CONTENT_FILE`. For
  backwards compatibility, `YAML_CONTENT` can still be used.

### Added

- Added an environment variable `YAML_CONTENT_STRING` so that data can be passed in
  string form rather than in file form.

- Improved concurrency handling by checking for resource conflicts when updating
  the config map.

- Improved the ability to update more specific portions of the config map by adding
  a recursive `merge_dict` utility that is used to merge input data into the existing
  config map.

## [1.6.0] - 2022-05-09

### Added

- Added new `query` module to query the `cray-product-catalog` K8s ConfigMap to
  obtain information about the installed products.

### Changed

- Relaxed schema for product data added to `cray-product-catalog` K8s ConfigMap
  to allow additional properties.

- Update base image to artifactory.algol60.net/csm-docker/stable/docker.io/library/alpine:3.15

- Update license text to comply with automatic license-check tool.

- Update deploy script to work with CSM 1.2 systems and Nexus authentication

### Fixed

- Fixed location where Python module and Helm chart are published to
  Artifactory by "Build Artifacts" GitHub Actions workflow.

## [1.5.5] - 2022-03-04

### Changed

- Update the image signing and software bill of materials github actions (Cray
  HPE internal actions) to use the preferred GCP authentication.

- CASMCMS-7878 - switch build artifacts workflow build-prep step to ubuntu
  public runner per GitHub security recommendations

- Update python dependencies

## [1.5.4] - 2022-02-15

### Changed

- Save build artifacts for default of 90 days

- Push all semver docker image tags, not just the image:x.y.z-builddate.commit tag

- Bump jfrog/setup-jfrog-cli from 1 to 2.1.0

- Bump cardinalby/git-get-release-action from 1.1 to 1.2.2

- Bump rsa from 4.7 to 4.8

- Bump python-dateutil from 2.7.5 to 2.8.2


## [1.5.3] - 2022-02-08

### Changed

- Use csm-changelog-checker and csm-gitflow-mergeback actions in common workflows

## [1.5.2] - 2022-02-02

### Removed

- Autoapprove PR action for gitflow mergeback PRs

## [1.5.1] - 2022-02-02

### Added

- Automerge capabilities for gitflow mergeback PRs

### Changed

- PR title in gitflow mergeback PRs is repo-specific so including them in
  release notes and in different repo PRs, they refer to original PRs

## [1.5.0] - 2022-02-01

### Added

- Added reference to Keep a Changelog format to README file

- Added reference to CSM Gitflow development process to README file

### Removed

- Remove redundant license/copyright info from README

## [1.4.23] - 2022-01-27

### Changed

- Restrict the changelog and artifact pr workflows to not run on gitflow and
  dependency update PRs

- dependabot update python dep attrs from 21.2.0 to 21.4.0

## [1.4.22] - 2022-01-27

### Changed

- Fixed gitflow mergeback workflow to use correct app key/id

## [1.4.21] - 2022-01-26

### Changed

- Let PR artifacts deploy workflow time out if it doesn't find a matching build

## [1.4.20] - 2022-01-26

### Changed

- Update gitflow mergeback workflow to use continuous update strategy

## [1.4.19] - 2022-01-26

### Added

- Add gitflow mergeback workflow

## [1.4.18] - 2022-01-26

### Added

- Allow Github releases to be updated when rebuilding tagged releases
  (for rebuilds to fix CVEs, etc)

## [1.4.17] - 2022-01-26

### Changed

- Fix release note rendering for stable releases

## [1.4.15] - 2022-01-25

### Changed

- Update to use new "no ref needed" reusable workflow

## [1.4.14] - 2022-01-21

### Added

- Update CSM manifest workflow

- Release workflow to build artifacts and create GH releases on tags

### Changed

- Build artifacts workflow is now reusable, no longer builds on tag events

### Removed

- Removed old and unused release prep workflows

## [1.4.13] - 2022-01-20

### Added

- Add changelog checker workflow

## [1.4.12] - 2022-01-19

- Test release with only CHANGELOG updates

## [1.4.11] - 2022-01-19

### Added

- Added workflows for finishing gitflow release and merging back to develop

## [1.4.10] - 2022-01-13

### Changed

- Only build artifacts on push events, not PRs. Change PR comments to point to the individual commit, not the overall PR.

## [1.4.6] - 2022-01-07

### Changed

- Fix the draft release PR workflow to add labels

## [1.4.5] - 2022-01-07

### Added

- Add workflows for creating PRs for a draft release, and tagging and release creation when a release branch is merged to master.

## [1.4.4] - 2022-01-07

### Added

- Build docker image, helm chart, python module with GH actions (CASMCMS-7698)

## [1.4.3] - 2022-01-05

### Changed

- Change default behavior to stop setting "active" key unless `SET_ACTIVE_VERSION` variable is given.

## 1.4.2 - 2021-12-01

### Changed

- Updated README to reflect versioning change in v1.4.1.

## 1.4.1 - 2021-12-01

### Changed

- Changed GitVersion.yml to ignore previous CSM release branches

## 1.4.0 - 2021-11-29

### Added

- Build docker image with CSM-provided build-scan-sign GH action

- Add GitVersion.yml for automatic git versioning using Gitflow

- Pull python requirements from PyPI, not arti.dev.cray.com to enable GH actions builds

## 1.3.1 - 2021-11-19

### Added

- Added pull request template

- Added Chart lint, test, scan action

### Changed

- Conformed chart to CASM-2670 specifications (CASMCMS-7619)

## 1.2.71 - 2017-11-15

### Added

- Included cray-product-catalog python module

- Introduce new catalog entry delete functionality

### Changed

- Updated repo to Gitflow branching strategy; develop branch now base branch

- Change default reviewers to CMS-core-product-support

[Unreleased]: https://github.com/Cray-HPE/cray-product-catalog-core/compare/v2.6.0...HEAD

[2.6.0]: https://github.com/Cray-HPE/cray-product-catalog-core/compare/v2.5.0...v2.6.0

[2.5.0]: https://github.com/Cray-HPE/cray-product-catalog-core/compare/5f4a2f8309e954807d7acc6e165308c2a0cd56ba...v2.5.0
