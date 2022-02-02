---
name: Subsequent Release Candidate Checklist (maintainer only)
about: Checklist template for all subsequent releases (RC 2-N, FINAL and PATCH) of every series
title: llvmlite X.Y.Z Checklist (FIXME)
labels: task

---


## llvmlite X.Y.Z
* [ ] Merge to `main` (when approved):
  * "any remaining PRs"
* [ ] Collect required PRs and create a PR with cherry-picks.
* [ ] Approve change log modifications and cherry-pick too.
* [ ] Merge change log modifications and cherry-picks to X.Y release branch.
  * [ ] "PR with cherry-picks and changelog for release branch"
* [ ] Annotated tag `vX.Y.Z` on release branch (`llvmlite` tags DO have a `v` prefix).
* [ ] Build conda packages on buildfarm (check "upload").
* [ ] Verify packages uploaded to Anaconda Cloud and move to `numba/label/main`.
* [ ] Build wheels (`$PYTHON_VERSIONS`) on the buildfarm.
* [ ] Upload wheels and sdist to PyPI and verify arrival. (upload from `ci_artifacts`).
* [ ] Verify ReadTheDocs build.
* [ ] Send RC/FINAL announcement email / post announcement to discourse group.
* [ ] Post link to Twitter.

### Post release

* [ ] Clean up `ci_artifacts` by moving files to subdirectories
* [ ] Update release checklist template.
* [ ] Ping Anaconda Distro team to trigger a build for `defaults` (FINAL ONLY).
* [ ] Close milestone (and then close this release issue).
