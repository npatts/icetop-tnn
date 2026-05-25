# IceTop-TNN
> What? IceTop-TNN? That's not a real thing!!! It's called a transformer.

## Requirements
IceTop-TNN requires Python 3.10+. If you are running on an IceCube node, you may need
to enable a more modern CVMFS version (and update environment.txt accordingly.)

## Setup
IceTop-TNN requires quite a bit of setup to get running at first. 
- Download the GraphNeT submodule with `git submodule sync --init`
- Copy the `environment.txt.example` file to `environment.txt` and update any
  values that you would like changed. The default values are intended for use
  on IceCube's computing system.
- Run the setup script `./tools/setup.sh` 

## Execution
If your workspace is set up correctly, the IceTop-TNN CLI can be invoked by running
```
python3 -m icetoptnn
```
