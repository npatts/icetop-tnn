# IceTop-TNN
> What? IceTop-TNN? That's not a real thing!!! It's called a transformer.

## Requirements
- Python 3.10+ \
  If you are running on an IceCube node, you may need
  to enable a more modern CVMFS version (and update environment.txt accordingly.)
- IceTray \
  GraphNeT requires an active IceTray environment in order to read i3 event files.
- pkg-config \
  For building h5py
- libhdf5 1.10.4+ \
  For h5py

## Setup
IceTop-TNN requires quite a bit of setup to get running at first. 
- Enable your IceTray environment. How to do this depends on if you're using it
  through CVMFS or if you've installed it manually.
- Download the GraphNeT submodule with `git submodule sync --init`
- Copy the `environment.txt.example` file to `environment.txt` and update any
  values that you would like changed. The default values are intended for use
  on IceCube's computing system.
- Run the setup script `./tools/setup.sh` 

## Execution
If your workspace is set up correctly, you are in an IceTray environment, and you are
in your venv (ICETOP_TNN_VENV_ROOT in your environment.txt file), the IceTop-TNN CLI
can be invoked by running

```
python3 -m icetoptnn
```
