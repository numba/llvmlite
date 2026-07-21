#!/usr/bin/env python3
"""Generate a release CHANGE_LOG section for llvmlite.

Auto-detects the latest ``vX.Y.0dev0`` tag as the start point, lists the
merged PRs since then (skipping any already in ``CHANGE_LOG``), and credits
every author including ``Co-authored-by:`` trailers.

Prints to stdout by default; pass ``--write`` to prepend the section to
``CHANGE_LOG``. Token comes from ``--token``, ``$GITHUB_TOKEN``/``$GH_TOKEN``,
or ``gh auth token``.

Examples:
  python generate_changelog.py
  python generate_changelog.py --write
  python generate_changelog.py --start v0.47.0 --repo numba/llvmlite
"""

import os
import re
import sys
import argparse
import subprocess
from datetime import date

from github import Github, Auth, GithubException

CHANGE_LOG = "CHANGE_LOG"
COAUTHOR_RE = re.compile(r"^Co-authored-by:\s*(.+?)\s*<(.+?)>", re.MULTILINE)
_EMAIL_CACHE = {}


def sh(*cmd):
    return subprocess.run(
        cmd, capture_output=True, text=True, check=False
    ).stdout.strip()


def detect_start():
    """Latest vX.Y.0dev0 tag, marking the start of the dev cycle."""
    tags = sh("git", "tag", "-l", "v*dev0", "--sort=-v:refname").split("\n")
    return next((t for t in tags if t), None)


def merged_pr_numbers(start):
    log = sh("git", "log", f"{start}..HEAD", "--oneline",
             "--grep", "Merge pull request")
    nums = {int(m.group(1)) for line in log.split("\n")
            if (m := re.search(r"#(\d+)", line))}
    return sorted(nums)


def known_pr_numbers(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return {int(n) for n in re.findall(r"PR `#(\d+)", fh.read())}
    except FileNotFoundError:
        return set()


def resolve_token(token):
    token = token or os.environ.get("GITHUB_TOKEN") or \
        os.environ.get("GH_TOKEN") or sh("gh", "auth", "token")
    assert token, ("No GitHub token: pass --token, set GITHUB_TOKEN, or "
                   "run `gh auth login`.")
    return token


def resolve_email(gh, email):
    """Map a co-author email to a GitHub user (login, url); name-only if not."""
    if email in _EMAIL_CACHE:
        return _EMAIL_CACHE[email]
    user = None
    try:
        if email.endswith("@users.noreply.github.com"):
            login = email.split("@")[0].split("+")[-1]
            user = gh.get_user(login)
        else:
            hits = gh.search_users(f"{email} in:email")
            user = hits[0] if hits.totalCount else None
    except GithubException:
        user = None
    _EMAIL_CACHE[email] = user
    return user


def pr_authors(gh, pr):
    """Set of (login_or_name, url_or_None) including co-author trailers."""
    authors = set()
    for c in pr.get_commits():
        if c.author:
            authors.add((c.author.login, c.author.html_url))
        if c.committer and c.committer.login != "web-flow":
            authors.add((c.committer.login, c.committer.html_url))
        for name, email in COAUTHOR_RE.findall(c.commit.message):
            user = resolve_email(gh, email)
            authors.add((user.login, user.html_url) if user else (name, None))
    return authors


def credit(login, url):
    return f"`{login} <{url}>`_" if url else login


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--start", help="Start tag/commit "
                        "(default: latest vX.Y.0dev0 tag)")
    parser.add_argument("--token", help="GitHub token (default: env/gh)")
    parser.add_argument("--repo", default="numba/llvmlite")
    parser.add_argument("--changelog", default=CHANGE_LOG)
    parser.add_argument("--write", action="store_true",
                        help="Prepend the section into CHANGE_LOG")
    args = parser.parse_args()

    start = args.start or detect_start()
    assert start, "Could not detect a vX.Y.0dev0 tag; pass --start."
    print(f"Start point: {start}", file=sys.stderr)

    known = known_pr_numbers(args.changelog)
    fresh = [n for n in merged_pr_numbers(start) if n not in known]
    skipped = [n for n in merged_pr_numbers(start) if n in known]
    if skipped:
        print(f"Skipping {len(skipped)} already in CHANGE_LOG: "
              f"{', '.join('#%d' % n for n in skipped)}", file=sys.stderr)
    assert fresh, "No new PRs to add after dedup."
    print(f"Including {len(fresh)} new PR(s)", file=sys.stderr)

    gh = Github(auth=Auth.Token(resolve_token(args.token)))
    repo = gh.get_repo(args.repo)

    pr_lines = []
    all_authors = set()
    for i, num in enumerate(fresh, 1):
        print(f"  [{i}/{len(fresh)}] PR #{num}", file=sys.stderr)
        pr = repo.get_pull(num)
        authors = pr_authors(gh, pr)
        all_authors |= authors
        names = " ".join(credit(*a) for a in
                         sorted(authors, key=lambda a: a[0].lower()))
        pr_lines.append(f"* PR `#{num} <{pr.html_url}>`_: {pr.title} ({names})")

    author_lines = [f"* {credit(*a)}" for a in
                    sorted(all_authors, key=lambda a: a[0].lower())]

    body = ("Pull-Requests:\n\n" + "\n".join(pr_lines) +
            "\n\nAuthors:\n\n" + "\n".join(author_lines) + "\n")

    if args.write:
        version = re.sub(r"^v|dev\d*$", "", start)
        header = f"v{version} ({date.today().strftime('%B %-d, %Y')})"
        section = (f"{header}\n{'-' * len(header)}\n\n"
                   "This release of llvmlite ... FIXME\n\n" + body + "\n")
        with open(args.changelog, encoding="utf-8") as fh:
            existing = fh.read()
        with open(args.changelog, "w", encoding="utf-8") as fh:
            fh.write(section + existing)
        print(f"Wrote v{version} section to {args.changelog}", file=sys.stderr)
    else:
        print("\n" + body)


if __name__ == "__main__":
    main()
