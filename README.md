# Symphony

TCP/IP server/client framework to orchestrate the execution of benchmarks on a traget device with Python 

## Introduction

This is a project to automate the process of testing benchmarks at different voltages. It includes classes and methods to manage the test process, collect and save results, and handle errors.

The project includes two main scripts, the host/host.py (client) an the target/dut.py (server).
The DUT runs the 

## Dependencies

- Python 3.x
- (Add any other libraries or dependencies required by your project)

## How to Use

1. Clone the repository to your local machine.
2. Install the required dependencies. We recomments to use the same python version on both the host and the target DUT
3. Run the `host/host.py` script on the host pc (i.e., the PC that will collect the data).
4. Run the `target/dut.py` script on the target board.

```bash
git clone git@github.com:unipieslab/symphony.git
cd symphony
sudo install-Pyhton3.9.1
```