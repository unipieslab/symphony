# Symphony

TCP/IP server/client framework to orchestrate the execution of benchmarks on a traget device with Python.

## Introduction

This is a project to automate the process of testing benchmarks at different voltages. It includes classes and methods to manage the test process, collect and save results, and handle errors.

![Figure 1](docs/figs/architecture.png)

In the `/docs` directory you can find information about the internal functions of Symphony and their usage



## Getting started 

Symphony consists of two parts. The Server and the client. In symphony's terminology these are the DUT(target) and the Host. The DUT executes `target/dut.py` that will monitor any essential information for the experiment. This information is sent in the Host that executes `host/host.py`. In order to start using Symphony, you need to setup both devices.

### How to setup

1. Install Symphony and dependencies in both devices (Host and DUT)

Clone the repository and navigate to the symphony directory:

````
git clone git@github.com:unipieslab/symphony.git

cd symphony
````

Next, depending on your Linux package manager, execute the appropriate script:

- For RedHat-based Linux, run:

````
$ chmod +x install-Python<VERSION>_dnf.sh
$ ./install-Python<VERSION>_dnf.sh
````

- For Debian-based Linux, run:

````
$ chmod +x install-Python<VERSION>_apt.sh
$ ./install-Python<VERSION>_apt.sh
````

Once these steps are successfully completed, Symphony and all its dependencies will be installed. 

2. Create the virtual environment and subfolders

**DUT only**

Navigate to `host` folder and run `createVenv.sh`

```
$ cd host
$./createVenv.sh
```


**Host Only**

In the `host` directory, build the venv and sub-folders

````
$ cd host
$ make
````

The environment is ready. 


To run Symphony,

1. In the DUT, execute `dut.py`

```
$ cd target
$ python3 dut.py
```

> *In the DUT, `dut.py` can be setup as a systemd service. Go to `target/README` for more information.*

2. In the **Host**, execute `host.py`

```
$ cd host
$ python3 host.py
```

> The libraries are installed in the `venv`, make sure you run symphony with the virtual environment activated.

Host will immediately attempt to connect to the DUT, if the component is up and running.

## Bug report
This is an open-source framework that can be used for executing experiments, thus we would appreciate any contribution in case a bug is found. Bug reports can be sent either by getting in contact with the framework's maintainers or by opening an issue in the current repository.
