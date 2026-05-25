#!/usr/bin/env bash

if ! [ -f ./environment.txt ]; then
    echo "ERROR: Unable to read environment.txt, are you at the repository root?" >> /dev/stderr;
    exit 1;
fi;
source ./environment.txt

if [ -z "$ICETOP_TNN_VENV_ROOT" ]; then
    echo "ERROR: ICETOP_TNN_VENV_ROOT is not set. Is your environment.txt set up correctly?" >> /dev/stderr;
    exit 1;
fi;
ICETOP_TNN_VENV_ROOT="$(realpath "$ICETOP_TNN_VENV_ROOT")"
if [ "$ICETOP_TNN_VENV_ROOT" = "/" -o "$ICETOP_TNN_VENV_ROOT" = "" -o "$ICETOP_TNN_VENV_ROOT" = "$(realpath "$HOME")" ]; then
    echo "ERROR: ICETOP_TNN_VENV_ROOT is "$ICETOP_TNN_VENV_ROOT". You probably do not want this." >> /dev/stderr;
    exit 1;
fi;

echo "Virtual environment root is $ICETOP_TNN_VENV_ROOT";

# set up venv
python3 -m venv "$ICETOP_TNN_VENV_ROOT"
source "$ICETOP_TNN_VENV_ROOT/bin/activate"

# install graphnet build tools
pip install setuptools==82.0 \
            packaging==26.0 \
            || exit 1;

# install pytorch
pip install --index-url https://download.pytorch.org/whl/cu128 \
            torch==2.7.0 \
            torchvision \
            torchaudio \
            || exit 1;

# build graphnet
pushd external/graphnet
    pip install -e '.[develop,torch-27]' -f https://data.pyg.org/whl/torch-2.7.0+cu128.html || exit 1;
popd
