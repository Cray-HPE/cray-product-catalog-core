# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Only build artifacts on push events, not PRs. Change PR comments to point to
  the individual commit, not the overall PR.

## [1.4.6] - 2022-01-07

-   Fix the draft release PR workflow to add labels

## [1.4.5] - 2022-01-07

### Added

-   Add workflows for creating PRs for a draft release, and tagging and release
    creation when a release branch is merged to master.

## [1.4.4] - 2022-01-07

### Added

-   Build docker image, helm chart, python module with GH actions (CASMCMS-7698)

## [1.4.3] - 2022-01-05

### Changed

-   Change default behavior to stop setting "active" key unless `SET_ACTIVE_VERSION`
    variable is given.

## 1.4.2 - 2021-12-01

### Changed

-   Updated README to reflect versioning change in v1.4.1.

## 1.4.1 - 2021-12-01

### Changed

-   Changed GitVersion.yml to ignore previous CSM release branches

## 1.4.0 - 2021-11-29

### Added

-   Build docker image with CSM-provided build-scan-sign GH action
-   Add GitVersion.yml for automatic git versioning using Gitflow
-   Pull python requirements from PyPI, not arti.dev.cray.com to enable GH actions builds

## 1.3.1 - 2021-11-19

### Added

-   Added pull request template
-   Added Chart lint, test, scan action

### Changed

-   Conformed chart to CASM-2670 specifications (CASMCMS-7619)

## 1.2.71 - 2017-11-15

### Added

-   Included cray-product-catalog python module
-   Introduce new catalog entry delete functionality

### Changed

-   Updated repo to Gitflow branching strategy; develop branch now base branch
-   Change default reviewers to CMS-core-product-support

[Unreleased]: https://github.com/Cray-HPE/cray-product-catalog/compare/1.4.6...HEAD

[1.4.6]: https://github.com/Cray-HPE/cray-product-catalog/compare/1.4.5...1.4.6

[1.4.5]: https://github.com/Cray-HPE/cray-product-catalog/compare/1.4.4...1.4.5

[1.4.4]: https://github.com/Cray-HPE/cray-product-catalog/compare/1.4.3...1.4.4

[1.4.3]: https://github.com/Cray-HPE/cray-product-catalog/compare/1.4.2...1.4.3