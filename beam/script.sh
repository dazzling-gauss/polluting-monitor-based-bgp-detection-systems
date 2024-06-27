#!/bin/bash

repo=https://github.com/yhchen-tsinghua/routing-anomaly-detection.git

script_dir=$(dirname "$0")
git clone $repo $script_dir/repos

# unzip demo data
old_dir=$(pwd)
cd $script_dir
cat demo_data_part_*.zip > demo_data_combined.zip
unzip -o demo_data_combined.zip
cd $old_dir