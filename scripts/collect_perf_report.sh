#!/bin/bash

set -e

CURRENT_DIR=$(pwd)
# Create a directory to store the perf_reports
mkdir -p $CURRENT_DIR/collected_perf_reports
mkdir -p $CURRENT_DIR/collected_vtune_reports
# Iterate over each directory in the current directory
for dir in $CURRENT_DIR/*; do
    if [ -d "$dir" ]; then
        # Get directory name
        dir_name=$(basename "$dir")
        if ls "$dir/${dir_name}"*.perf_report.csv 1> /dev/null 2>&1; then
            # Copy the perf_report Directory to the collected_perf_reports directory
            echo -e "Copying $dir/${dir_name}*.perf_report.csv to $CURRENT_DIR/collected_perf_reports"
            cp -r $dir/${dir_name}*.perf_report.csv $CURRENT_DIR/collected_perf_reports
        fi
        if ls "$dir/${dir_name}"*.perf_report.txt 1> /dev/null 2>&1; then
            # Copy the perf_report Directory to the collected_perf_reports directory
            echo -e "Copying $dir/${dir_name}*.perf_report.txt to $CURRENT_DIR/collected_perf_reports"
            cp -r $dir/${dir_name}*.perf_report.txt $CURRENT_DIR/collected_perf_reports
        fi
        if ls "$dir/${dir_name}"*.vtune.csv 1> /dev/null 2>&1; then
            # Copy the perf_report Directory to the collected_vtune_reports directory
            echo -e "Copying $dir/${dir_name}"*.vtune.csv to $CURRENT_DIR/collected_vtune_reports"
            cp -r $dir/${dir_name}"*.vtune.csv $CURRENT_DIR/collected_vtune_reports
        fi
    fi
done