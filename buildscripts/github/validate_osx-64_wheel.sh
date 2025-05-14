#!/bin/bash

set -ex

# This script assumes it is run from the directory containing the wheels.

shopt -s nullglob # Prevent loop from running if no *.whl files

for WHL_FILE in *.whl; do
  echo "=== Validating $WHL_FILE ==="

  # Check wheel structure
  twine check "$WHL_FILE"

  # Check dylib paths
  wheel unpack "$WHL_FILE"
  WHEEL_DIR=$(echo "$WHL_FILE" | cut -d "-" -f1 -f2)
  DYLIB=$(find "$WHEEL_DIR" -iname "libllvmlite.dylib")

  if [ -z "$DYLIB" ]; then
    echo "Error: libllvmlite.dylib not found in $WHL_FILE"
    exit 1
  fi

  echo "=== Checking dynamic library dependencies for $WHL_FILE ==="
  otool -L "$DYLIB"

  # Verify library paths
  LIBS=("libz.1.dylib" "libc++.1.dylib")
  for LIB in "${LIBS[@]}"; do
    if ! otool -L "$DYLIB" | grep -q "/usr/lib/$LIB"; then
      echo "Error: $LIB path is incorrect in $WHL_FILE"
      # Clean up unpacked directory before exiting
      rm -rf "$WHEEL_DIR"
      exit 1
    fi
  done

  # Clean up unpacked directory
  echo "=== Cleaning up $WHEEL_DIR ==="
  rm -rf "$WHEEL_DIR"

done

echo "=== Validation successful ==="
