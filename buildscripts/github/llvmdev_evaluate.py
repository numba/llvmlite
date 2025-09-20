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
        "recipe": "llvmdev",
    },
    {
        "runner": runner_mapping["linux-64"],
        "platform": "linux-64",
        "recipe": "llvmdev_for_wheel",
    },
    # linux-aarch64
    {
        "runner": runner_mapping["linux-aarch64"],
        "platform": "linux-aarch64",
        "recipe": "llvmdev",
    },
    {
        "runner": runner_mapping["linux-aarch64"],
        "platform": "linux-aarch64",
        "recipe": "llvmdev_for_wheel",
    },
    # osx-arm64
    {
        "runner": runner_mapping["osx-arm64"],
        "platform": "osx-arm64",
        "recipe": "llvmdev",
    },
    {
        "runner": runner_mapping["osx-arm64"],
        "platform": "osx-arm64",
        "recipe": "llvmdev_for_wheel",
    },
    # win-64
    {
        "runner": runner_mapping["win-64"],
        "platform": "win-64",
        "recipe": "llvmdev",
    },
    {
        "runner": runner_mapping["win-64"],
        "platform": "win-64",
        "recipe": "llvmdev_for_wheel",
    },
]

print(
    "Deciding what to do based on event: "
    f"'{event}', label: '{label}', inputs: '{inputs}'"
)
if event == "pull_request":
    print("pull_request detected")
    include = default_include
elif event == "label" and label == "build_on_gha":
    print("build label detected")
    include = default_include
elif event == "workflow_dispatch":
    print("workflow_dispatch detected")
    params = json.loads(inputs)
    platform = params.get("platform", "all")
    recipe = params.get("recipe", "all")

    # Start with the full matrix
    filtered_matrix = default_include

    # Filter by platform if a specific one is chosen
    if platform != "all":
        filtered_matrix = [
            item for item in filtered_matrix if item["platform"] == platform
        ]

    # Filter by recipe if a specific one is chosen
    if recipe != "all":
        filtered_matrix = [
            item for item in filtered_matrix if item["recipe"] == recipe
        ]

    include = filtered_matrix
else:
    include = {}

matrix = {"include": include}
print(f"Emitting matrix:\n {json.dumps(matrix, indent=4)}")

Path(os.environ["GITHUB_OUTPUT"]).write_text(f"matrix={json.dumps(matrix)}")
