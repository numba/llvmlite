#!/usr/bin/env python
"""Find successful llvmlite workflow run IDs for a given git tag."""

import argparse
import json
import os
import subprocess
import sys


def find_workflow_run(workflow_name, tag, repo, token):
    """
    Find the latest successful workflow run for a given workflow and tag.

    Args:
        workflow_name: Name of the workflow file (e.g., 'llvmlite_conda_builder.yml')
        tag: Git tag to search for
        repo: Repository in format 'owner/repo' (e.g., 'numba/llvmlite')
        token: GitHub token for API authentication

    Returns:
        Run ID as a string, or None if not found
    """
    print(f"Search for successful run of {workflow_name} on tag {tag} in {repo}", file=sys.stderr)

    env = os.environ.copy()
    env['GH_TOKEN'] = token

    try:
        result = subprocess.run(
            [
                "gh", "api",
                "-H", "Accept: application/vnd.github+json",
                "-H", "X-GitHub-Api-Version: 2022-11-28",
                f"/repos/{repo}/actions/workflows/{workflow_name}/runs",
                "--jq", f'.workflow_runs[] | select(.head_branch == "{tag}" and .conclusion == "success") | .id'
            ],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        run_ids = result.stdout.strip().split('\n')
        if run_ids and run_ids[0]:
            run_id = run_ids[0]
            print(f"Found run ID {run_id} for {workflow_name}", file=sys.stderr)
            return run_id

        print(f"ERROR: No successful run found for {workflow_name} on tag {tag}", file=sys.stderr)
        return None

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to query GitHub API: {e}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Find successful workflow run IDs for a given tag'
    )
    parser.add_argument(
        '--tag',
        default=os.environ.get('TAG', ''),
        help='Git tag to search for (default: TAG env var)'
    )
    parser.add_argument(
        '--repo',
        default=os.environ.get('GITHUB_REPOSITORY', 'numba/llvmlite'),
        help='Repository in format owner/repo (default: GITHUB_REPOSITORY env var or numba/llvmlite)'
    )
    parser.add_argument(
        '--token',
        default=os.environ.get('GH_TOKEN', os.environ.get('GITHUB_TOKEN', '')),
        help='GitHub token for API authentication (default: GH_TOKEN or GITHUB_TOKEN env var)'
    )

    args = parser.parse_args()

    if not args.tag:
        parser.error("TAG is required (via --tag or TAG env var)")
    if not args.token:
        parser.error("GitHub token is required (via --token or GH_TOKEN/GITHUB_TOKEN env var)")

    # Define workflow groups
    conda_workflow = "llvmlite_conda_builder.yml"
    wheel_workflows = [
        "llvmlite_linux-64_wheel_builder.yml",
        "llvmlite_linux-aarch64_wheel_builder.yml",
        "llvmlite_osx-arm64_wheel_builder.yml",
        "llvmlite_win-64_wheel_builder.yml",
    ]

    all_found = True

    # find conda workflow run
    print("=== finding conda workflow run ===", file=sys.stderr)
    conda_run_id = find_workflow_run(conda_workflow, args.tag, args.repo, args.token)
    if not conda_run_id:
        all_found = False
        print(f"WARNING: Could not find run ID for {conda_workflow}", file=sys.stderr)

    # find wheel workflow runs
    print("\n=== finding wheel workflow runs ===", file=sys.stderr)
    wheel_run_ids = []
    for workflow_file in wheel_workflows:
        run_id = find_workflow_run(workflow_file, args.tag, args.repo, args.token)
        if run_id:
            wheel_run_ids.append(run_id)
        else:
            all_found = False
            print(f"WARNING: Could not find run ID for {workflow_file}", file=sys.stderr)

    if not all_found:
        print("\nERROR: Not all workflow runs were found", file=sys.stderr)
        sys.exit(1)

    print("\n=== found workflow run IDs ===", file=sys.stderr)
    print(f"conda: {conda_run_id}", file=sys.stderr)
    print(f"wheels: {' '.join(wheel_run_ids)}", file=sys.stderr)

    # pass run IDs to subsequent steps via GITHUB_OUTPUT
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"conda_run_id={conda_run_id}\n")
            f.write(f"wheel_run_ids={' '.join(wheel_run_ids)}\n")
    else:
        # print to stdout when not running in a github action workflow
        print("\nWARNING: GITHUB_OUTPUT not set", file=sys.stderr)


if __name__ == "__main__":
    main()

