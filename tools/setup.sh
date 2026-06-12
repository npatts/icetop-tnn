#!/usr/bin/env bash

# load environment.txt
if ! [ -f ./environment.txt ]; then
    echo "ERROR: Unable to read environment.txt, are you at the repository root?" >> /dev/stderr;
    exit 1;
fi;
source ./environment.txt

# check venv root
if [ -z "$ICETOP_TNN_VENV_ROOT" ]; then
    echo "ERROR: ICETOP_TNN_VENV_ROOT is not set. Is your environment.txt set up correctly?" >> /dev/stderr;
    exit 1;
fi;
ICETOP_TNN_VENV_ROOT="$(realpath "$ICETOP_TNN_VENV_ROOT")"
if [ "$ICETOP_TNN_VENV_ROOT" = "/" -o "$ICETOP_TNN_VENV_ROOT" = "" -o "$ICETOP_TNN_VENV_ROOT" = "$(realpath "$HOME")" ]; then
    echo "ERROR: ICETOP_TNN_VENV_ROOT is "$ICETOP_TNN_VENV_ROOT". You probably do not want this." >> /dev/stderr;
    exit 1;
fi;

# check that python and pip work
if PYTHON_VERSION="$(! "$PYTHON_EXECUTABLE" --version)"; then
    echo "ERROR: Unable to execute PYTHON_EXECUTABLE" >> /dev/stderr
    exit 1
fi;

# echo executables
echo "Initializing IceTop-TNN up with the following environment:"
echo "  Virtual environment root is $ICETOP_TNN_VENV_ROOT";
echo "  Python executable is $PYTHON_EXECUTABLE ($PYTHON_VERSION)";

# set up venv
"$PYTHON_EXECUTABLE" -m venv "$ICETOP_TNN_VENV_ROOT"
source "$ICETOP_TNN_VENV_ROOT/bin/activate"

# install python build tools
"$PYTHON_EXECUTABLE" -m pip install setuptools==82.0 \
                          packaging==26.0 \
                          || exit 1;

# build h5py from source. if the h5py library does not match the hdf5 version the library will fail to initialize properly.
"$PYTHON_EXECUTABLE" -m pip install --no-binary h5py h5py==3.16.0 || exit 1;

# install pytorch
"$PYTHON_EXECUTABLE" -m pip install --index-url https://download.pytorch.org/whl/cu128 \
                  torch==2.7.0 \
                  torchvision \
                  torchaudio \
                  || exit 1;

# install pycondor and pyyaml
"$PYTHON_EXECUTABLE" -m pip install pycondor==0.6.1 pyyaml==6.0.3 || exit 1;

# build graphnet
pushd external/graphnet
    "$PYTHON_EXECUTABLE" -m pip install -e '.[develop,torch-27]' -f https://data.pyg.org/whl/torch-2.7.0+cu128.html || exit 1;
popd
