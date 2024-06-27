#!/bin/bash
base_url="https://forge.icube.unistra.fr/tholterbach/"

# List of repositories to clone
repos=(
    # "dfoh_database" - not needed for the attacks
    # "dfoh_newedge"
    # "dfoh_sampling"
    "dfoh_peeringdb"
    "dfoh_topological"
    "dfoh_bidirectionality"
    "dfoh_aspathpattern"
    "dfoh_inference"
)

script_dir=$(dirname "$0")

echo "Cloning repositories from $base_url"
echo "Cloning into $script_dir"

for repo in "${repos[@]}"; do
    if [ -d "$script_dir/repos/$repo" ]; then
        echo "Repository $repo already exists, skipping"
        continue
    fi

    echo "Cloning $repo"
    git clone "$base_url$repo.git" $script_dir/repos/$repo
done

# Build each dockerfile in the repositories
curr_dir=$(pwd)
for repo in "${repos[@]}"; do
    echo "Building $repo"
    cd "$script_dir/repos/$repo"

    # if repo is dfoh_aspathpattern, change the tagname to dfoh_aspathfeat
    if [ "$repo" == "dfoh_aspathpattern" ]; then
        repo="dfoh_aspathfeat"
    fi

    sudo docker build -t "$repo" -f docker/Dockerfile .
    cd $curr_dir
done