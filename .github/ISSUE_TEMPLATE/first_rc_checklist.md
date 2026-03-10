---
name: First Release Candidate Checklist (maintainer only)
about: Checklist template for the first release of every series
title: llvmlite X.Y.Zrc1 Checklist (FIXME)
labels: task

---

## llvmlite X.Y.Z

This is the release checklist for the first release candidate llvmlite
X.Y.Zrc1. 

This list is to be used by the release manager to keep track of what needs
doing and to communicate to the community the progress of the release. Add
checkmarks when a task is done and supply links for builds, packages, tags,
built documentation etc by editing the list.

You can use the `<strike>` and `</strike>` syntax to eliminate tasks, but add a
note in the list as to why they were eliminated.

Lastly see the notes below for hints and details.

### Main Release Tasks:

* [ ] Merge to `main`.
    * [ ] "remaining Pull-Requests from milestone".
* In case of an LLVM upgrade:
    * [ ] Check if the compatibility matrix in the `README.rst` needs updating.
    * [ ] Check if the inter-sphinx link in `llvmlite/docs/source/conf.py`
          needs an update.
    * [ ] Create a PR targeting `main` (and have it reviewed and merged)
          should any of the above apply.
* [ ] Create X.Y release branch `releaseX.Y`
    * [ ] Update `CHANGE_LOG` in a PR targeting the release branch.
    * [ ] Use the script `maint/gitlog2changelog.py` from Numba.
    * [ ] Follow the format of previous `CHANGE_LOG` entries.
* [ ] Have the change-log-PR reviewed and merged.
* [ ] Test `HEAD` of release branch on GHA (pre-tag testing).
* [ ] Test `HEAD` of release branch on conda-forge.
* [ ] Annotated tag `vX.Y.Zrc1` on release branch (`llvmlite` tags DO have a `v` prefix).
* [ ] Build conda packages and wheels on GHA.
* [ ] Upload conda packages and wheels.
* [ ] Verify conda packages and wheels have arrived.
* [ ] Initialize and verify ReadTheDocs (RTD) build.
* [ ] Send RC announcement email / post announcement to discourse group.
* [ ] Post link to X and Mastodon and anywhere else that is appropriate.

### Post Release Tasks:

* [ ] Tag X.Y+1.0dev0 to start new development cycle on `main`.
* [ ] Build conda packages and wheels on GHA using `vX.Y+1.0dev0` tag.
* [ ] Upload packages for dev tag to anaconda.org dev label:
  ```
  gh workflow run .github/workflows/upload_packages.yml \
    --field tag="vX.Y+1.0dev0" \
    --field anaconda_label="dev"
  ```
  Note: This uploads packages and wheels to anaconda.org dev label only (no copy to main, no PyPI upload).
* [ ] Update release checklist template with any additional bullet points that
      may have arisen during the release.
* [ ] Close milestone (and then close this release issue).


### Notes

* The release branch is created before updating the change-log. You can use the
  following command to initialize the release branch with an empty commit.
  ```
  gh commit --allow-empty "initialize releaseX.Y"  # replace X.Y
  ```
* When updating the changelog also update the version number at the top (for
  the release currently in progress)
* The tag is set using the command:
  ```
  git tag -am "Version X.Y.Z" "vX.Y.Zrc1"  # replace X.Y.Zrc1
  ```
* Instructions for running GHA jobs can be found at:
  https://github.com/numba/numba/wiki/Numba-CI-GitHub-Actions-Workflow-guide
  and some preliminary notes can be found below.
* Notes on uploading packages can be found below.
* To initialize the ReadTheDocs build, log into the web interface at
  https://app.readthedocs.org/ and activate the desired build.
* You can use the previous announcements on numba.discourse.group as a guide
  for future announcements.
* If you are unsure about anything, please reach out to previous release
  managers and ask for details.

### GHA Notes

This section details how GHA was run during the 0.45.0 release. These
instructions may be outdated and/or incomplete by the time you read this and
are to be considered as inspiration only. The commands use the `gh` command
line tool and assume a) that you have authenticated and that b) your shell has
the root of your local llvmlite clone as present working directory.

* Launching all jobs, two commands, replace `X` with branch or tag as
  appropriate, for example `release0.45` or `0.45.0`
  ```
  # This launches all conda builds:
  gh workflow run .github/workflows/llvmlite_conda_builder.yml --ref X -f platform=all
  # This launches all wheel builds:
  ls --color=never -1 .github/workflows/llvmlite_*_wheel_builder* | while read line ; do echo $line && gh workflow run $line --ref X ; done ;
  ```

### Uploading Notes

There are two artifact repositories that packages need to be uploaded to
anaconda.org and pypi.org.

* Automated Upload

Use the automated upload workflow to handle all uploads:

```
gh workflow run .github/workflows/upload_packages.yml \
  --field tag="vX.Y.Zrc1" \
  --field anaconda_label="dev" \
  --field copy_conda_to_main="true" \
  --field publish_to_pypi="true"
```

Replace `vX.Y.Zrc1` with the actual tag (e.g., `v0.46.0rc1`). This workflow will:
* Find all successful conda and wheel build runs for the given tag
* Download artifacts (conda packages and wheels) from those runs
* Upload conda packages and wheels to anaconda.org (dev label)
* Copy conda packages to main label (if `copy_conda_to_main` is true)
* Publish wheels to PyPI (if `publish_to_pypi` is true)

Monitor the workflow run in the GitHub Actions tab to verify successful completion.

* Manual Upload (Fallback)

If the automated workflow is unavailable, use these manual steps:

* Find and download artifacts from workflow runs:
  * First, find successful workflow runs for the tag (replace `vX.Y.Zrc1` with actual tag):
    ```
    export TAG="vX.Y.Zrc1"
    export GITHUB_REPOSITORY="numba/llvmlite"
    export GH_TOKEN="your_github_token"
    
    OUTPUT=$(./buildscripts/github/find_workflow_runs.py \
      --tag "$TAG" \
      --repo "$GITHUB_REPOSITORY" \
      --token "$GH_TOKEN" \
      --config ./buildscripts/github/workflow_groups.json)
    
    # Extract run IDs from output
    eval "$OUTPUT"
    ```
  * Download conda packages:
    ```
    ./buildscripts/github/download_artifacts.py \
      --run-ids $conda_run_ids \
      --repo "$GITHUB_REPOSITORY" \
      --token "$GH_TOKEN" \
      --output-dir conda_packages
    ```
  * Download wheels:
    ```
    ./buildscripts/github/download_artifacts.py \
      --run-ids $wheel_run_ids \
      --repo "$GITHUB_REPOSITORY" \
      --token "$GH_TOKEN" \
      --output-dir dist
    ```

* Upload to anaconda.org.
  * This uses the command line tool `anaconda` which can be installed using
    `conda install anaconda-client`.
  * This needs a suitable upload token from anaconda.org which can be generated
    from the web interface.
  * The packages are first uploaded to the label `dev` using the command below.
  * Once you are certain that file have arrived on `dev` use the web interface
    to copy them to `main`.
  * The command to upload is then (where `nu-XXX` is the token and `$PACKAGES`
    is a suitable shell glob):
    ```
    anaconda -t nu-XXX upload -u numba -l dev --force --no-register $PACKAGES
    ```

* Uploading to pypi.org
  * This uses the command line tool `twine` which can be installed using `conda
    install twine`.
  * This needs a suitable API token from pypi.org that can be generated from
    the web interface.
  * The command to upload is then (where `pypi-XXX` is the token and `$PACKAGES`
    is a suitable shell glob):
    ```
    twine upload -u __token__ -p pypi-XXX $PACKAGES
    ```
