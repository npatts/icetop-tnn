#!/usr/bin/env bash

# path
if [ -z "$ICETOPTNN_ENVIRONMENT_PATH" ]; then
    ICETOPTNN_ENVIRONMENT_PATH=./environment.txt
fi;

# load environment.txt
if ! [ -f "$ICETOPTNN_ENVIRONMENT_PATH" ]; then
    echo "ERROR: Unable to read $ICETOPTNN_ENVIRONMENT_PATH, are you at the repository root?" >> /dev/stderr;
    exit 1;
fi;
source $ICETOPTNN_ENVIRONMENT_PATH

# rebuild graphnet
pushd external/graphnet
    "$PIP_EXECUTABLE" install --ignore-installed --no-binary graphnet -e '.[develop,torch-27]' -f https://data.pyg.org/whl/torch-2.7.0+cu128.html \
                                                 --no-binary h5py h5py==3.16.0 \
                                                 || exit 1;
popd
