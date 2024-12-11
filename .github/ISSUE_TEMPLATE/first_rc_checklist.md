---
name: First Release Candidate Checklist (maintainer only)
about: Checklist template for the first release of every series
title: llvmlite X.Y.Zrc1 Checklist (FIXME)
labels: task

---


## llvmlite X.Y.Z

* [ ] Merge to `main`.
    * [ ] "remaining Pull-Requests from milestone".
* In case of an LLVM upgrade:
    * [ ] Check if the compatability matrix in the `README.rst` needs updating.
    * [ ] Check if the inter-sphinx link in `llvmlite/docs/source/conf.py`
          needs an update.
* [ ] Create X.Y release branch `releaseX.Y`
    * [ ] Update `CHANGE_LOG` in a PR targeting the release branch.
    * [ ] Follow the format of previous `CHANGE_LOG` entries.
* [ ] Get the change-log-PR reviewed and merged.
* [ ] Test `HEAD` of release branch on buildfarm (pre-tag testing):
    * [ ] conda package build and test.
    * [ ] wheel build.
* [ ] Test `HEAD` of release branch on conda-forge
* [ ] Annotated tag `vX.Y.Zrc1` on release branch (`llvmlite` tags DO have a `v` prefix).
* [ ] Build and upload conda packages on buildfarm (check "upload").
* [ ] Build wheels and sdist on the buildfarm (check "upload").
* [ ] Verify packages uploaded to Anaconda Cloud and copy to `numba/label/main`.
* [ ] Upload wheels and sdist to PyPI. (upload from `ci_artifacts`).
* [ ] Verify wheels for all platforms arrived on PyPi.
* [ ] Initialize and verify ReadTheDocs build.
* [ ] Send RC announcement email / post announcement to discourse group.
* [ ] Post link to X and Mastodon and anywhere else that is appropriate.

### Post Release:

* [ ] Clean up `ci_artifacts` by moving files to subdirectories
* [ ] Tag X.Y+1.0dev0 to start new development cycle on `main`.
* [ ] Update release checklist template with any additional bullet points that
      may have arisen during the release.
* [ ] Close milestone (and then close this release issue).
