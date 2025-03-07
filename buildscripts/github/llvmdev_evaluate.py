#!/usr/bin/env python

import json
import os
from pathlib import Path
import subprocess

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

def setup_macos_sdk():
    """Setup macOS SDK for osx-64 builds"""
    print("Setting up macOS SDK for osx-64 build")
    sdk_dir = Path("buildscripts/github")
    sdk_dir.mkdir(parents=True, exist_ok=True)
    
    # Download SDK
    print("Downloading MacOSX10.10.sdk.tar.xz")
    subprocess.run(["wget", "-q", "https://github.com/phracker/MacOSX-SDKs/releases/download/11.3/MacOSX10.10.sdk.tar.xz"], 
                  check=True)
    
    # Verify checksum
    print("Verifying SDK checksum")
    subprocess.run(["shasum", "-c", "buildscripts/github/MacOSX10.10.sdk.checksum"], 
                  check=True)
    
    # Extract SDK
    print("Extracting SDK")
    subprocess.run(["tar", "-xf", "MacOSX10.10.sdk.tar.xz"], 
                  check=True)
    
    # Set environment variables
    sdk_path = str(Path.cwd() / "MacOSX10.10.sdk")
    os.environ["SDKROOT"] = sdk_path
    os.environ["CONDA_BUILD_SYSROOT"] = sdk_path
    os.environ["macos_min_version"] = "10.10"
    os.environ["CFLAGS"] = f"-isysroot {sdk_path} {os.environ.get('CFLAGS', '')}"
    os.environ["CXXFLAGS"] = f"-isysroot {sdk_path} {os.environ.get('CXXFLAGS', '')}"
    os.environ["LDFLAGS"] = f"-Wl,-syslibroot,{sdk_path} {os.environ.get('LDFLAGS', '')}"
    os.environ["CMAKE_OSX_SYSROOT"] = sdk_path
    os.environ["CMAKE_OSX_DEPLOYMENT_TARGET"] = "10.10"
    print("macOS SDK setup complete")

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

# Setup platform-specific requirements
if any(job["platform"] == "osx-64" for job in include):
    setup_macos_sdk()

matrix = {"include": include}
print(f"Emitting matrix:\n {json.dumps(matrix, indent=4)}")

Path(os.environ["GITHUB_OUTPUT"]).write_text(f"matrix={json.dumps(matrix)}")
