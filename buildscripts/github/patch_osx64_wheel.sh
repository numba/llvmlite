#!/bin/bash

set -ex

WHL_FILE="$1"

echo "Processing wheel: $WHL_FILE"

# Unpack the wheel
wheel unpack "$WHL_FILE"

# Get into the unpacked directory
target_dir=$(echo "$WHL_FILE" | cut -d "-" -f1 -f2)
cd "$target_dir"

# Find the dylib
target=$(find . -iname "libllvmlite.dylib")
echo "Found dylib at: $target"

echo "=== BEFORE ==="
otool -L "$target"

# Fix all @rpath libraries
install_name_tool -change "@rpath/libz.1.dylib" "/usr/lib/libz.1.dylib" "$target"
install_name_tool -change "@rpath/libc++.1.dylib" "/usr/lib/libc++.1.dylib" "$target"

echo "=== AFTER ==="
otool -L "$target"

echo "=== $target_dir contents ==="
find . -ls
echo "=== Write back to wheel ==="
cd ..
wheel pack "$target_dir"

# Remove the directory we unpacked into
rm -rf "$target_dir"

echo "=== Final wheel filename ==="
ls -la ./*.whl
