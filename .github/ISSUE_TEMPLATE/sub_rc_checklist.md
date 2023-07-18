---
name: Subsequent Release Candidate Checklist (maintainer only)
about: Checklist template for all subsequent releases (RC 2-N, FINAL and PATCH) of every series
title: llvmlite X.Y.Z Checklist (FIXME)
labels: task

---


## llvmlite X.Y.Z

* [ ] Cherry-pick items from the X.Y.Z milestone into a PR targeting the release branch.
* [ ] Update `CHANGE_LOG` on cherry-pick-PR.
* [ ] Have cherry-pick-PR reviewed and merged.
* [ ] Test `HEAD` of release branch on buildfarm (pre-tag testing):
  * [ ] conda package build and test.
  * [ ] wheel build.
* [ ] Annotated tag `vX.Y.Z` on release branch (`llvmlite` tags DO have a `v` prefix).
* [ ] Build and upload conda packages on buildfarm (check "upload").
* [ ] Build wheels and sdist on the buildfarm (check "upload").
* [ ] Verify packages uploaded to Anaconda Cloud and move to `numba/label/main`.
* [ ] Upload wheels and sdist to PyPI. (upload from `ci_artifacts`).
* [ ] Verify wheels for all platforms arrived on PyPi.
* [ ] Verify ReadTheDocs build.
* [ ] Send RC/FINAL announcement email / post announcement to discourse group.
* [ ] Post link to Twitter and Mastodon and anywhere else that is appropriate.

### Post release

* [ ] Cherry-pick changes to the `CHANGE_LOG` to `main`
* [ ] Clean up `ci_artifacts` by moving files to subdirectories
* [ ] Update release checklist template with any additional bullet points that
      may have arisen during the release.
* [ ] Ping Anaconda Distro team to trigger a build for `defaults` (FINAL ONLY).
* [ ] Close milestone (and then close this release issue).
