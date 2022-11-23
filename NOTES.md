# Notes about ukbb_cardiac toolbox

github repo: https://github.com/gouzhuang/ukbb_cardiac
forked from: https://github.com/baiwenjia/ukbb_cardiac

## Additions to the original toolbox

### 1. [data/convert_data.py](data/convert_data.py)

**Usage:**
```sh
python3 data/convert_data.py <data_dir> [<output_dir>]
```

if `<output_dir>` is omitted, the default is `<data_dir>.converted`, which is at the save level as `<data_dir>`.
`<output_dir>` will be created if it does not exist

**structure of input data dir:**
```text
<data_dir>/
     |
     +--<subject_id1>/
     |       |
     |       +--<subject_id1>_cvi42.zip
     |       +--<subject_id1>_long.zip
     |       +--<subject_id1>_short.zip
     |
     +--<subject_id2>/
     |       |
     |       +--<subject_id2>_cvi42.zip
     |       +--<subject_id2>_long.zip
     |       +--<subject_id2>_short.zip
    ...    
```

**structure of output dir:**
```text
<output_dir>/
     |
     +--<subject_id1>/
     |       |
     |       +--la_2ch.nii.gz
     |       +--la_3ch.nii.gz
     |       +--la_4ch.nii.gz
     |       +--sa.nii.gz
     |       +--label_*.nii.gz (optional)
     |
     +--<subject_id2>/
     |       |
    ...     ...
```

### 2. [predict.py](predict.py)

**Usage:**
```sh
python3 predict.py <data_dir>
```
where `<data_dir>` contains the converted data(output of [`data/convert_data.py`](data/convert_data.py))

output csv files are placed at `<data_dir>.output_csv` at the same level as `<data_dir>`

## Environment setup

2 options available to try out the toolbox

### Option#1: Using Conda environment(Recommended)

1. create conda environment
```sh
conda env create -f ukbb-conda-env.yml
```

content of ukbb-conda-env.yml:
```yaml
name: ukbb
dependencies:
  - python=3.6
  - ipython
  - jupyter
  - tensorflow-gpu=1.15.*
```

2. install additional modules

```sh
% conda activate ukbb
(ukbb) % pip install -r requirements.txt
```

content of requirements.txt:
```txt
pandas
python-dateutil
scikit-image
scipy
seaborn
vtk
pydicom
nibabel
opencv-python
SimpleITK
```

3. clone src code from github
```sh
% cd notebooks
% git clone https://github.com/gouzhuang/ukbb_cardiac.git
```

4. prepare demo data

copy demo_csv, demo_image, trained_model into notebooks/ukbb_cardiac/

5. run the demo

```
(ukbb) % export PYTHONPATH=$(realpath ./notebooks)
(ukbb) % cd notebooks/ukbb_cardiac
(ukbb) % python3 demo_pipeline.py
```

### Option#2: Using Docker
#### Customizing the docker image

1. start a tensorflow container as current user
```sh
docker run -it \
    -u $(id -u):$(id -g) \
    -v $(realpath ./notebooks):/tf/notebooks \
    -p 8888:8888 \
    --gpus all \
    --name tf_base \
    tensorflow/tensorflow:1.15.5-gpu-py3-jupyter
```

The output should look like this:
```
% docker run -it -u $(id -u):$(id -g) -v $(realpath ./notebooks):/tf/notebooks -p 8888:8888 --gpus all --name tf_base tensorflow/tensorflow:1.15.5-gpu-py3-jupyter

________                               _______________                
___  __/__________________________________  ____/__  /________      __
__  /  _  _ \_  __ \_  ___/  __ \_  ___/_  /_   __  /_  __ \_ | /| / /
_  /   /  __/  / / /(__  )/ /_/ /  /   _  __/   _  / / /_/ /_ |/ |/ / 
/_/    \___//_/ /_//____/ \____//_/    /_/      /_/  \____/____/|__/


You are running this container as user with ID 1000 and group 1000,
which should map to the ID and group for your user on the Docker host. Great!

[I 02:37:20.203 NotebookApp] Writing notebook server cookie secret to /.local/share/jupyter/runtime/notebook_cookie_secret
/usr/local/lib/python3.6/dist-packages/IPython/paths.py:67: UserWarning: IPython parent '/' is not a writable location, using a temp directory.
  " using a temp directory.".format(parent))
[I 02:37:20.378 NotebookApp] Serving notebooks from local directory: /tf
[I 02:37:20.378 NotebookApp] Jupyter Notebook 6.1.6 is running at:
[I 02:37:20.378 NotebookApp] http://19bd321b39b8:8888/?token=c2dead89189ae0a449f6ffadb406b8a6ce59721d5704a205
[I 02:37:20.378 NotebookApp]  or http://127.0.0.1:8888/?token=c2dead89189ae0a449f6ffadb406b8a6ce59721d5704a205
[I 02:37:20.378 NotebookApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
[C 02:37:20.382 NotebookApp] 
    
    To access the notebook, open this file in a browser:
        file:///.local/share/jupyter/runtime/nbserver-1-open.html
    Or copy and paste one of these URLs:
        http://19bd321b39b8:8888/?token=c2dead89189ae0a449f6ffadb406b8a6ce59721d5704a205
     or http://127.0.0.1:8888/?token=c2dead89189ae0a449f6ffadb406b8a6ce59721d5704a205
```
2. exec bash as root into the container
```sh
% docker exec -it --user root tf_base /bin/bash

________                               _______________                
___  __/__________________________________  ____/__  /________      __
__  /  _  _ \_  __ \_  ___/  __ \_  ___/_  /_   __  /_  __ \_ | /| / /
_  /   /  __/  / / /(__  )/ /_/ /  /   _  __/   _  / / /_/ /_ |/ |/ / 
/_/    \___//_/ /_//____/ \____//_/    /_/      /_/  \____/____/|__/


WARNING: You are running this container as root, which can cause new files in
mounted volumes to be created as the root user on your host machine.

To avoid this, run the container by specifying your user's userid:

$ docker run -u $(id -u):$(id -g) args...

root@19bd321b39b8:/tf# 
```

3. install additional packages
```sh
root@19bd321b39b8:/tf# apt update; apt install -y libx11-6 libgl1 libxrender1
```

4. exit the root shell
```sh
root@19bd321b39b8:/tf# exit
```

5. exec bash as current user into the container
```sh
% docker exec -it tf_base /bin/bash

________                               _______________                
___  __/__________________________________  ____/__  /________      __
__  /  _  _ \_  __ \_  ___/  __ \_  ___/_  /_   __  /_  __ \_ | /| / /
_  /   /  __/  / / /(__  )/ /_/ /  /   _  __/   _  / / /_/ /_ |/ |/ / 
/_/    \___//_/ /_//____/ \____//_/    /_/      /_/  \____/____/|__/


You are running this container as user with ID 1000 and group 1000,
which should map to the ID and group for your user on the Docker host. Great!

tf-docker /tf > 
```

6. install additional python modules
```sh
tf-docker /tf > pip3 install scipy seaborn pandas python-dateutil \
    pydicom SimpleITK nibabel scikit-image opencv-python-headless vtk
```

7. commit the docker image
```sh
% docker commit tf_base tensorflow-custom
% docker tag tensorflow-custom:latest tensorflow-custom:1.15.5-gpu-py3-jupyter
```

8. stop the container
```sh
% docker stop tf_base
```

#### Using customized image

1. start a container from the customized image
```sh
% docker run -it \
    -u $(id -u):$(id -g) \
    -v $(realpath ./notebooks):/tf/notebooks \
    -p 8888:8888 \
    --gpus all \
    --name ukbb \
    tensorflow-custom:1.15.5-gpu-py3-jupyter
```
You can access the jupyter notebook by clicking the URL printed out

2. check out the code into the notebooks directory
```sh
% cd notebooks
% git clone https://github.com/gouzhuang/ukbb_cardiac.git
```

3. prepare demo data

copy demo_csv, demo_image, trained_model into notebooks/ukbb_cardiac

4. run the demo

- login to the container
```sh
% docker exec -it ukbb /bin/bash
```

- run the demo
```sh
tf-docker /tf > export PYTHONPATH=/tf/notebooks
tf-docker /tf > cd notebooks/ukbb_cardiac
tf-docker /tf/notebooks/ukbb_cardiac > python3 demo_pipeline.py
```