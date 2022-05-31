---
name: First Release Candidate Checklist (maintainer only)
about: Checklist template for the first release of every series
title: llvmlite X.Y.Zrc1 Checklist (FIXME)
labels: task

---


## llvmlite X.Y.Z

* [ ] Merge to `main`.
    - [ ] "remaining Pull-Requests from milestone".
* [ ] Merge change log changes.
    - [ ] "PR with changelog entries".
* [ ] Create X.Y release branch `releaseX.Y`
* [ ] Annotated tag `vX.Y.Z` on release branch (`llvmlite` tags DO have a `v` prefix).
* [ ] Build conda packages on buildfarm (check "upload").
* [ ] Verify packages uploaded to Anaconda Cloud and move to `numba/label/main`.
* [ ] Build wheels and sdist (`$PYTHON_VERSIONS`) on the buildfarm.
* [ ] Upload wheels and sdist to PyPI and verify arrival. (upload from `ci_artifacts`).
* [ ] Initialize and verify ReadTheDocs build.
* [ ] Send RC announcement email / post announcement to discourse group.
* [ ] Post link to Twitter.

### Post Release:

* [ ] Clean up `ci_artifacts`.
* [ ] Update release checklist template with any additional bullet points that
      may have arisen during the release.
* [ ] Close milestone (and then close this release issue).
