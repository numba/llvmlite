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
    "osx-64": "macos-13",
    "osx-arm64": "macos-14",
    "win-64": "windows-2019",
}

default_include = [
    # {
    #     "runner": runner_mapping["linux-64"],
    #     "platform": "linux-64",
    #     "recipe": "llvmdev",
    # },
    # {
    #     "runner": runner_mapping["win-64"],
    #     "platform": "win-64",
    #     "recipe": "llvmdev",
    # },
    # {
    #     "runner": runner_mapping["win-64"],
    #     "platform": "win-64",
    #     "recipe": "llvmdev_for_wheel",
    # },
    {
        "runner": runner_mapping["osx-64"],
        "platform": "osx-64",
        "recipe": "llvmdev",
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
    include = [
        {
            "runner": runner_mapping[params.get("platform", "linux-64")],
            "platform": params.get("platform", "linux-64"),
            "recipe": params.get("recipe", "llvmdev"),
        }
    ]
else:
    include = {}

matrix = {"include": include}
print(f"Emitting matrix:\n {json.dumps(matrix, indent=4)}")

Path(os.environ["GITHUB_OUTPUT"]).write_text(f"matrix={json.dumps(matrix)}")
