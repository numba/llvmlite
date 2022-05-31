# This file helps to compute a version number in source trees obtained from
# git-archive tarball (such as those provided by githubs download-from-tag
# feature). Distribution tarballs (built by setup.py sdist) and build
# directories (produced by setup.py build) will contain a much shorter file
# that just contains the computed version number.

from __future__ import annotations

# This file is released into the public domain. Generated by
# versioneer-0.12 (https://github.com/warner/python-versioneer)
# these strings will be replaced by git during git-archive
git_refnames = "$Format:{}$"
git_full = "$Format:%H$"

# these strings are filled in when 'setup.py versioneer' creates _version.py
tag_prefix = "v"
parentdir_prefix = "llvmlite-"
versionfile_source = "llvmlite/_version.py"

import errno
import os
import re
import subprocess
import sys


def run_command(
    commands: list[str],
    args: list[str],
    cwd: str | None = None,
    verbose: bool = False,
    hide_stderr: bool = False,
) -> str | None:
    assert isinstance(commands, list)
    p = None
    for c in commands:
        try:
            # remember shell=False, so use git.cmd on windows, not just git
            p = subprocess.Popen(
                [c] + args,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=(subprocess.PIPE if hide_stderr else None),
            )
            break
        except EnvironmentError:
            e = sys.exc_info()[1]
            if e.errno == errno.ENOENT:  # type: ignore
                continue
            if verbose:
                print(f"unable to run {args[0]}")
                print(e)
            return None
    else:
        if verbose:
            print(f"unable to find command, tried {commands}")
        return None
    stdout = p.communicate()[0].strip()
    if sys.version >= "3":
        stdout = stdout.decode()  # type: ignore
    if p.returncode != 0:
        if verbose:
            print(f"unable to run {args[0]} (error)")
        return None
    return stdout  # type: ignore


def versions_from_parentdir(
    parentdir_prefix: str, root: str, verbose: bool = False
) -> dict[str, str] | None:
    # Source tarballs conventionally unpack into a directory that includes
    # both the project name and a version string.
    dirname = os.path.basename(root)
    if not dirname.startswith(parentdir_prefix):
        if verbose:
            print(
                f"guessing rootdir is '{root}', but '{dirname}' doesn't start with prefix '{parentdir_prefix}'"
            )
        return None
    return {"version": dirname[len(parentdir_prefix) :], "full": ""}


def git_get_keywords(versionfile_abs: str) -> dict[str, str]:
    # the code embedded in _version.py can just fetch the value of these
    # keywords. When used from setup.py, we don't want to import _version.py,
    # so we do it with a regexp instead. This function is not used from
    # _version.py.
    keywords: dict[str, str] = {}
    try:
        f = open(versionfile_abs, "r")
        for line in f.readlines():
            if line.strip().startswith("git_refnames ="):
                mo = re.search(r'=\s*"(.*)"', line)
                if mo:
                    keywords["refnames"] = mo.group(1)
            if line.strip().startswith("git_full ="):
                mo = re.search(r'=\s*"(.*)"', line)
                if mo:
                    keywords["full"] = mo.group(1)
        f.close()
    except EnvironmentError:
        pass
    return keywords


def git_versions_from_keywords(
    keywords: dict[str, str], tag_prefix: str, verbose: bool = False
) -> dict[str, str] | None:
    if not keywords:
        return {}  # keyword-finding function failed to find keywords
    refnames = keywords["refnames"].strip()
    if refnames.startswith("$Format"):
        if verbose:
            print("keywords are unexpanded, not using")
        return {}  # unexpanded, so not in an unpacked git-archive tarball
    refs = set([r.strip() for r in refnames.strip("()").split(",")])
    # starting in git-1.8.3, tags are listed as "tag: foo-1.0" instead of
    # just "foo-1.0". If we see a "tag: " prefix, prefer those.
    TAG = "tag: "
    tags = set([r[len(TAG) :] for r in refs if r.startswith(TAG)])
    if not tags:
        # Either we're using git < 1.8.3, or there really are no tags. We use
        # a heuristic: assume all version tags have a digit. The old git {}
        # expansion behaves like git log --decorate=short and strips out the
        # refs/heads/ and refs/tags/ prefixes that would let us distinguish
        # between branches and tags. By ignoring refnames without digits, we
        # filter out many common branch names like "release" and
        # "stabilization", as well as "HEAD" and "master".
        tags = set([r for r in refs if re.search(r"\d", r)])
        if verbose:
            print("discarding '{}', no digits".format(",".join(refs - tags)))
    if verbose:
        print("likely tags: {}".format(",".join(sorted(tags))))
    for ref in sorted(tags):
        # sorting will prefer e.g. "2.0" over "2.0rc1"
        if ref.startswith(tag_prefix):
            r = ref[len(tag_prefix) :]
            if verbose:
                print("picking {}".format(r))
            return {"version": r, "full": keywords["full"].strip()}
    # no suitable tags, so we use the full revision id
    if verbose:
        print("no suitable tags, using full revision id")
    return {"version": keywords["full"].strip(), "full": keywords["full"].strip()}


def git_versions_from_vcs(
    tag_prefix: str, root: str, verbose: bool = False
) -> dict[str, str]:
    # this runs 'git' from the root of the source tree. This only gets called
    # if the git-archive 'subst' keywords were *not* expanded, and
    # _version.py hasn't already been rewritten with a short version string,
    # meaning we're inside a checked out source tree.

    if not os.path.exists(os.path.join(root, ".git")):
        if verbose:
            print(f"no .git in {root}")
        return {}

    gits = ["git"]
    if sys.platform == "win32":
        gits = ["git.cmd", "git.exe"]
    stdout = run_command(gits, ["describe", "--tags", "--dirty", "--always"], cwd=root)
    if stdout is None:
        return {}
    if not stdout.startswith(tag_prefix):  # type: ignore
        if verbose:
            print("tag '{}' doesn't start with prefix '{}'".format(stdout, tag_prefix))
        return {}
    tag = stdout[len(tag_prefix) :]
    stdout = run_command(gits, ["rev-parse", "HEAD"], cwd=root)
    if stdout is None:
        return {}
    full = stdout.strip()
    if tag.endswith("-dirty"):  # type: ignore
        full += "-dirty"  # type: ignore
    return {"version": tag, "full": full}  # type: ignore


def get_versions(
    default: dict[str, str] = {"version": "unknown", "full": ""}, verbose: bool = False
) -> dict[str, str]:
    # I am in _version.py, which lives at ROOT/VERSIONFILE_SOURCE. If we have
    # __file__, we can work backwards from there to the root. Some
    # py2exe/bbfreeze/non-CPython implementations don't do __file__, in which
    # case we can only use expanded keywords.

    keywords = {"refnames": git_refnames, "full": git_full}
    ver = git_versions_from_keywords(keywords, tag_prefix, verbose)
    if ver:
        return ver

    try:
        root = os.path.abspath(__file__)
        # versionfile_source is the relative path from the top of the source
        # tree (where the .git directory might live) to this file. Invert
        # this to find the root from __file__.
        for _ in range(len(versionfile_source.split(os.sep))):
            root = os.path.dirname(root)
    except NameError:
        return default

    return (
        git_versions_from_vcs(tag_prefix, root, verbose)
        or versions_from_parentdir(parentdir_prefix, root, verbose)
        or default
    )
