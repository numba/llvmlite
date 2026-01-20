#!/usr/bin/env python

import json
import os
from pathlib import Path


event = os.environ.get("GITHUB_EVENT_NAME")
label = os.environ.get("GITHUB_LABEL_NAME")
inputs = os.environ.get("GITHUB_WORKFLOW_INPUT", "{}")

runner_mapping = {
    "linux-64": "ubuntu-24.04",
    "linux-aarch64": "ubuntu-24.04-arm",
    "osx-arm64": "macos-14",
    "win-64": "windows-2025",
}

default_include = [
    # linux-64
    {
        "runner": runner_mapping["linux-64"],
        "platform": "linux-64",
        "python-version": "3.10"
    },
    {
        "runner": runner_mapping["linux-64"],
        "platform": "linux-64",
        "python-version": "3.11"
    },
    {
        "runner": runner_mapping["linux-64"],
        "platform": "linux-64",
        "python-version": "3.12"
    },
    {
        "runner": runner_mapping["linux-64"],
        "platform": "linux-64",
        "python-version": "3.13"
    },
    {
        "runner": runner_mapping["linux-64"],
        "platform": "linux-64",
        "python-version": "3.14"
    },

    # linux-aarch64
    {
        "runner": runner_mapping["linux-aarch64"],
        "platform": "linux-aarch64",
        "python-version": "3.10"
    },
    {
        "runner": runner_mapping["linux-aarch64"],
        "platform": "linux-aarch64",
        "python-version": "3.11"
    },
    {
        "runner": runner_mapping["linux-aarch64"],
        "platform": "linux-aarch64",
        "python-version": "3.12"
    },
    {
        "runner": runner_mapping["linux-aarch64"],
        "platform": "linux-aarch64",
        "python-version": "3.13"
    },
    {
        "runner": runner_mapping["linux-aarch64"],
        "platform": "linux-aarch64",
        "python-version": "3.14"
    },

    # osx-arm64
    {
        "runner": runner_mapping["osx-arm64"],
        "platform": "osx-arm64",
        "python-version": "3.10"
    },
    {
        "runner": runner_mapping["osx-arm64"],
        "platform": "osx-arm64",
        "python-version": "3.11"
    },
    {
        "runner": runner_mapping["osx-arm64"],
        "platform": "osx-arm64",
        "python-version": "3.12"
    },
    {
        "runner": runner_mapping["osx-arm64"],
        "platform": "osx-arm64",
        "python-version": "3.13"
    },
    {
        "runner": runner_mapping["osx-arm64"],
        "platform": "osx-arm64",
        "python-version": "3.14"
    },

    # win-64
    {
        "runner": runner_mapping["win-64"],
        "platform": "win-64",
        "python-version": "3.10"
    },
    {
        "runner": runner_mapping["win-64"],
        "platform": "win-64",
        "python-version": "3.11"
    },
    {
        "runner": runner_mapping["win-64"],
        "platform": "win-64",
        "python-version": "3.12"
    },
    {
        "runner": runner_mapping["win-64"],
        "platform": "win-64",
        "python-version": "3.13"
    },
    {
        "runner": runner_mapping["win-64"],
        "platform": "win-64",
        "python-version": "3.14"
    },
]

print(
    "Deciding what to do based on event: "
    f"'{event}', label: '{label}', inputs: '{inputs}'"
)
if event in ("pull_request", "push", "schedule"):
    # This condition is entered on pull requests, pushes, and scheduled runs.
    # The controlling workflow filters push events to only the `main` branch.
    # See `on.push.branches` in `.github/workflows/llvmlite_conda_builder.yml`.
    print(f"{event} detected, running full build matrix.")
    include = default_include
elif event == "label" and label == "build_llvmlite_on_gha":
    print("build label detected")
    include = default_include
elif event == "workflow_dispatch":
    print("workflow_dispatch detected")
    params = json.loads(inputs)
    platform = params.get("platform", "all")

    # Start with the full matrix
    filtered_matrix = default_include

    # Filter by platform if a specific one is chosen
    if platform != "all":
        filtered_matrix = [
            item for item in filtered_matrix if item["platform"] == platform
        ]

    include = filtered_matrix
else:
    # For any other events, produce an empty matrix.
    include = []

matrix = {"include": include}
print(f"Emitting matrix:\n {json.dumps(matrix, indent=4)}")

Path(os.environ["GITHUB_OUTPUT"]).write_text(f"matrix={json.dumps(matrix)}")
