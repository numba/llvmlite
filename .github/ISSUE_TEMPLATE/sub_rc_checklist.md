---
name: Subsequent Release Candidate Checklist (maintainer only)
about: Checklist template for all subsequent releases (RC 2-N, FINAL and PATCH) of every series
title: llvmlite X.Y.Z Checklist (FIXME)
labels: task

---


## llvmlite X.Y.Z

This is the release checklist for the second release candidate llvmlite
X.Y.Zrc2, for any subsequent release candidate and for the FINAL release.

This list is to be used by the release manager to keep track of what needs
doing and to communicate to the community the progress of the release. Add
checkmarks when a task is done and supply links for builds, packages, tags,
built documentation etc by editing the list.

You can use the `<strike>` and `</strike>` syntax to eliminate tasks, but add a
note in the list as to why they were eliminated.

Lastly see the notes below for hints and details.

### Main Release Tasks:

* [ ] Merge to `releaseX.Y`.
    * [ ] "remaining Pull-Requests from milestone".
    * [ ] Cherry-pick any needed CI hot-fixes from `main`.
* [ ] Update `CHANGE_LOG` in a PR targeting `releaseX.Y`.
* [ ] Test `HEAD` of release branch on GHA (pre-tag testing).
* [ ] Test `HEAD` of release branch on conda-forge.
* [ ] Annotated tag `vX.Y.Z` on release branch (`llvmlite` tags DO have a `v` prefix).
* [ ] Build conda packages and wheels on GHA.
* [ ] Upload conda packages and wheels.
* [ ] Verify conda packages and wheels have arrived
    * [ ] conda packages in `numba/label/main` on anaconda.org
    * [ ] wheels as a new version on PyPi
* [ ] Verify ReadTheDocs build.
* [ ] Create Github release at https://github.com/numba/llvmlite/releases using the tag.
* [ ] Send RC/FINAL announcement email / post announcement to discourse group.

### Post release

* [ ] Cherry-pick all merge commits that have been made to the `releaseX.Y`
      branch since it has been bifurcated from `main` and prepare a PR with
      these cherry-picks that targets `main`. (FINAL ONLY)
* [ ] Update release checklist template with any additional bullet points that
      may have arisen during the release.
* [ ] Ping Anaconda Distro team to trigger a build for `defaults` (FINAL ONLY).
* [ ] Close milestone (and then close this release issue).

### Notes

* See the notes in the first release candidate checklist regarding tagging,
  running GHA workflows, downloading and uploading packages
* You can cherry-pick merge commits using `git cherry-pick -m 1 $COMMIT`.
* The final change-log update PR has a chicken and egg problem. You need to
  first update the version number and release date in a first commit, then open
  a PR, then add exactly that PR to the change-log. This is where the PR must
  add itself to the changelog and that can not happen until it has been opened
  and has been assigned a number.
