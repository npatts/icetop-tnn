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
source $ICETOPTNN_ENVIRONMENT_ROOT

if ! [ -d "$CVMWRAP_CVMFS_PATH" -a -d "$CVMWRAP_CVMFS_PATH/metaprojects/icetray/$CVMWRAP_ICETRAY_VERSION" ]; then
    echo "ERROR: Unable to start IceTray environment";
    exit 1;
fi

# activate cvmfs
eval $($CVMWRAP_CVMFS_PATH/setup.sh);

$CVMWRAP_CVMFS_PATH/icetray-env icetray/$CVMWRAP_ICETRAY_VERSION $@
