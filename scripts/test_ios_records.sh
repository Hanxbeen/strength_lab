#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
test_output_dir=$(mktemp -d /tmp/mugemuge-swift-tests.XXXXXX)
trap 'rm -rf "$test_output_dir"' EXIT
sources=(apps/ios/MugeMuge/Models.swift apps/ios/MugeMuge/TrainingState.swift
apps/ios/MugeMuge/WorkoutReasons.swift apps/ios/MugeMuge/Services.swift
apps/ios/MugeMuge/StrengthMetrics.swift apps/ios/MugeMuge/CloudTransport.swift
apps/ios/MugeMuge/CloudMerge.swift apps/ios/MugeMuge/CloudThreeWayMerge.swift apps/ios/MugeMuge/CloudSyncPlan.swift)
for test_source in apps/ios/Tests/*.swift; do
  test_name=$(basename "$test_source" .swift)
  swiftc "${sources[@]}" "$test_source" -o "$test_output_dir/$test_name"
  "$test_output_dir/$test_name"
done
