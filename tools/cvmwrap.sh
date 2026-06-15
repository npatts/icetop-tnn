#!/usr/bin/env bash

# load environment.txt
if ! [ -f ./environment.txt ]; then
    echo "ERROR: Unable to read environment.txt, are you at the repository root?" >> /dev/stderr;
    exit 1;
fi;
source ./environment.txt

if ! [ -d "$CVMWRAP_CVMFS_PATH" -a -d "$CVMWRAP_CVMFS_PATH/metaprojects/icetray/$CVMWRAP_ICETRAY_VERSION" ]; then
    echo "ERROR: Unable to start IceTray environment";
    exit 1;
fi

# activate cvmfs
eval $($CVMWRAP_CVMFS_PATH/setup.sh);

$CVMWRAP_CVMFS_PATH/icetray-env icetray/$CVMWRAP_ICETRAY_VERSION $@
