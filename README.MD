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

## Data Conversion

GraphNeT cannot use raw i3 files when training models, instead, they first have to
be converted into a format that is compatible with GraphNeT, which it can then load
into a dataset while training. Dataset conversion can be extremely slow, so it is
helpful to split the task into multiple jobs and combine the converted dataset at
the end. 

You can create a dataset with IceTop-TNN using the `data create` subcommand. The
most basic invocation takes an empty output directory and an input file containing
a list of event files to include.

In order to run the dataset conversion task on a condor cluster, you can add the `-C`
argument. When running on condor, you can use the `--job-size`, `--job-count`, and
`--job-limit` arguments to specify the maximum amount of data a job can process,
the maximum number of files a job can process, and the maximum number of conversion 
jobs to submit. When finished, conversion jobs store converted data in the CONDOR_SCRATCH_DIR
specified in the environment file, which can be overridden with the `--condor-scratch`
argument. All other condor files are stored in the directories specified by the other
`--condor-*` arguments. The dataset generation jobs expect to be launched from a
directory present on every node, and may fail if they are not.

GraphNeT expects data to be laid out in a specific way, so IceTop-TNN uses symbolic
links to automatically arrange files in a way that can be used with GraphNeT. Data 
input files are YAML files containing a list of event files and GCDs that should
be included in the data conversion task. They all follow the following structure:

```yml
# Groups are a list of multiple files. All of their contents will be included in
# the conversion task.
!tnn/group # Each part is tagged with !tnn/group or !tnn/file to specify what class
           # they represent
contents:
  # GCD files are !tnn/file objects with the resource key set to GCD. They are used for
  # event files with whichever layout is specified in the layout key. You can not specify
  # a directory in the path.
- !tnn/file
  path:     /data/ana/CosmicRay/IceTop_level3/sim/IC86.2012/GCD/Level3_12362_GCD.i3.gz
  layout:   12362
  resource: GCD

  # Event files are regular !tnn/file objects. They use the GCD file associated with the
  # layout specified in the layout key. The path can point to a file or directory.
- !tnn/file
  path:     /data/ana/CosmicRay/IceTop_level3/sim/IC86.2012/SIBYLL2.1/Fe/12362_v1s/
  layout:   12362
```

### Issues/Quirks

- The data converter has no way to recover from a worker job failing, if a job does not
  run correctly, the data conversion process must be restarted.
- The data conversion jobs are hard-coded to request 8GB of memory, which may be overkill
  for small tasks or when using a large number of jobs.
- If a job is requested with multiple cpu cores, the data converter will use more resources
  than what is allocated to it, so each job runs on a single cpu.
- Not a bug, but the data converter automatically removes NaN values from the dataset.

## Training & Evaluation

The evaluation subcommand is currently unfinished, so evaluation is currently done as
part of the training step. 

At the moment, the model architecture is hard-coded in the training subcommand. I plan
to set up a system similar to that of IceTop-CNN so that custom model architectures can
be loaded and used for training in the future. Training is far less developed than data
conversion.

Training takes a single dataset and uses the hyperparameters specified on the command
line. You can use a GPU to train the model by specifying the pytorch GPU number associated
with that GPU.

You can use the `-S` argument to filter the dataset and use only data that matches the
specified selection. IceTop-TNN uses GraphNeT's SQLite backend, so the selection string is
a SQLite condition that is spliced into the query. You can see the source query in the
`query_table` method in the `SQLiteDataset` class.

You can set the seeds that IceTop-TNN uses for training with the `--seed` and `--split-seed`
arguments. `--seed` sets the seed passed to `pytorch_lightning.seed_everything` and impacts
the model's final weights. `--split-seed` changes how the dataset is split, it defaults to
a constant defined in the trainer code.

The model weights and evaulation results are stored in the specified output directory.
Additionally, a model configuration file that can be used to load the model into GraphNeT
is also saved as `config.yml`. IceTop-TNN has its own model information file, `model.yml`,
which is also saved to the output directory. The data that is stored in `model.yml` can be
found in the `icetoptnn/training/training_info.py` file.

### Issues/Quirks

- As stated previously, evaluation happens during training, so in order to re-evaluate
  the model, you must train a new one. This will be fixed eventually.
- At the moment, you can only use a single dataset when training.
- There is no way to run training on a condor cluster, it has to be performed locally.
- The training script does not save checkpoints, so if training is interrupted, it will
  have to be restarted.
