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
if ! "$PYTHON_EXECUTABLE" --version; then
    echo "ERROR: Unable to execute PYTHON_EXECUTABLE" >> /dev/stderr
    exit 1
fi;
if ! "$PIP_EXECUTABLE" --version; then
    echo "ERROR: Unable to execute PIP_EXECUTABLE" >> /dev/stderr
    exit 1
fi;

echo "Virtual environment root is $ICETOP_TNN_VENV_ROOT";
echo "Python executable is $PYTHON_EXECUTABLE";
echo "Pip executable is $PIP_EXECUTABLE";

# set up venv
"$PYTHON_EXECUTABLE" -m venv "$ICETOP_TNN_VENV_ROOT"
source "$ICETOP_TNN_VENV_ROOT/bin/activate"

# install graphnet build tools
"$PIP_EXECUTABLE" install setuptools==82.0 \
                          packaging==26.0 \
                          || exit 1;

# install pytorch
"$PIP_EXECUTABLE" install --index-url https://download.pytorch.org/whl/cu128 \
                  torch==2.7.0 \
                  torchvision \
                  torchaudio \
                  || exit 1;

# build graphnet
pushd external/graphnet
    "$PIP_EXECUTABLE" install -e '.[develop,torch-27]' -f https://data.pyg.org/whl/torch-2.7.0+cu128.html || exit 1;
popd
