#!/usr/bin/env bash

# load environment.txt
if ! [ -f ./environment.txt ]; then
    echo "ERROR: Unable to read environment.txt, are you at the repository root?" >> /dev/stderr;
    exit 1;
fi;
source ./environment.txt

# rebuild graphnet
pushd external/graphnet
    "$PIP_EXECUTABLE" install --ignore-installed --no-binary graphnet -e '.[develop,torch-27]' -f https://data.pyg.org/whl/torch-2.7.0+cu128.html \
                                                 --no-binary h5py h5py==3.16.0 \
                                                 || exit 1;
popd
