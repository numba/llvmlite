#!/usr/bin/env python

import json
import os
from pathlib import Path


event = os.environ.get("GITHUB_EVENT_NAME")
label = os.environ.get("GITHUB_LABEL_NAME")
inputs = os.environ.get("GITHUB_WORKFLOW_INPUT", "{}")
changed_files = os.environ.get("ALL_CHANGED_FILES", "").split()

runner_mapping = {
    "linux-64": "ubuntu-24.04",
    "linux-aarch64": "ubuntu-24.04-arm",
    "osx-64": "macos-13",
    "osx-arm64": "macos-14",
    "win-64": "windows-2019",
}
print(f"runner_mapping: {runner_mapping}")

default_include = [
    {
        "runner": runner_mapping["win-64"],
        "rebuild_llvmdev": False,
        "platform": "win-64",
        "recipe": "llvmdev",
        "type": "conda",
    },
    {
        "runner": runner_mapping["win-64"],
        "rebuild_llvmdev": True,
        "platform": "win-64",
        "recipe": "llvmdev",
        "type": "wheel",
    },
]

print(
    f"Generationg matrix based on, event: '{event}', "
    f"label: '{label}', inputs: '{inputs}' ",
    f"changed_files: {changed_files}",
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
            "rebuild_llvmdev": True,
            "platform": params.get("platform", "win-64"),
            "recipe": "llvmdev",
            "type": "conda",
        },
        {
            "runner": runner_mapping[params.get("platform", "linux-64")],
            "rebuild_llvmdev": True,
            "platform": params.get("platform", "win-64"),
            "recipe": "llvmdev",
            "type": "wheel",
        },
    ]
else:
    include = {}

print(f"Emitting matrix:\n {json.dumps(include, indent=4)}")

Path(os.environ["GITHUB_OUTPUT"]).write_text(f"matrix={json.dumps(include)}")
