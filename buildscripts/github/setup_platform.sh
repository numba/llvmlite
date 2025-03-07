#!/bin/bash

set -x

PLATFORM=$1

echo "Setting up platform-specific requirements for ${PLATFORM}"

case "${PLATFORM}" in
    "osx-64")
        echo "Setting up macOS SDK for osx-64 build"
        sdk_dir="buildscripts/github"
        mkdir -p "${sdk_dir}"

        # Download SDK
        echo "Downloading MacOSX10.10.sdk.tar.xz"
        wget -q https://github.com/phracker/MacOSX-SDKs/releases/download/11.3/MacOSX10.10.sdk.tar.xz

        # Verify checksum
        echo "Verifying SDK checksum"
        shasum -c "${sdk_dir}/MacOSX10.10.sdk.checksum"

        # Extract SDK
        echo "Extracting SDK"
        tar -xf MacOSX10.10.sdk.tar.xz

        # Set environment variables
        sdk_path="$(pwd)/MacOSX10.10.sdk"
        export SDKROOT="${sdk_path}"
        export CONDA_BUILD_SYSROOT="${sdk_path}"
        export macos_min_version="10.10"
        export CFLAGS="-isysroot ${sdk_path} ${CFLAGS:-}"
        export CXXFLAGS="-isysroot ${sdk_path} ${CXXFLAGS:-}"
        export LDFLAGS="-Wl,-syslibroot,${sdk_path} ${LDFLAGS:-}"
        export CMAKE_OSX_SYSROOT="${sdk_path}"
        export CMAKE_OSX_DEPLOYMENT_TARGET="10.10"
        echo "macOS SDK setup complete"
        ;;
    "linux-64")
        echo "Setting up Linux-specific requirements"
        # Add Linux-specific setup here if needed
        ;;
    "linux-aarch64")
        echo "Setting up Linux ARM64-specific requirements"
        # Add Linux ARM64-specific setup here if needed
        ;;
    "osx-arm64")
        echo "Setting up macOS ARM64-specific requirements"
        # Add macOS ARM64-specific setup here if needed
        ;;
    "win-64")
        echo "Setting up Windows-specific requirements"
        # Add Windows-specific setup here if needed
        ;;
    *)
        echo "No specific setup required for platform: ${PLATFORM}"
        ;;
esac

echo "Platform setup complete for ${PLATFORM}" 