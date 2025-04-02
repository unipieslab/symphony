# Symphony user manual

## Introduction 
The provided user manual is associated with a Python-based framework called Symphony, which is utilized for conducting radiation-based experiments. Difficulty and safety during such experiments are the most significant factors; thus, Symphony is designed to prevent human interference, using the network infrastructure and various micro-controllers, like Raspberry Pi, to control situations that otherwise would demand humans to interfere.
The forenamed framework uses the client-server architecture to acquire the necessary features. This architecture typically uses two distinct systems, one that plays the role of the server side and the other that plays the role of the client side. Both the server and client, according to Symphony’s terminology, can be referred to with a unique name. The server side can be called Device Under Test (DUT), while the Client side is the Host.

Symphony lets users customize the necessities required for an experiment. The framework provides the user with an API to instruct Symphony to handle certain crucial situations.
The Sympohy’s API provides the following basic functionalities for radiation experiments:
•	A way to define the benchmarks to execute during the experiment
•	A way to handle crucial situations, such as kernel panic, crashes, and more (as depicted Table 1).
•	Give the user the freedom to choose what to do in the most common situations expected in such an experiment (through some callbacks, which will be covered later).
•	Saves the results in easy process JSON files.

## Architecture 
Symphony’s architecture uses the Client-Server network model. As the model suggests, it uses the network infrastructure to establish a connection between two systems, one located inside the radiation room, called Device Under Test (DUT), and the other that controls the DUT device from outside, called Host. The Host is responsible for the client-side operations, while the DUT is responsible for the server side.
![Figure 1](docs/figs/architecture.png)
The architecture of Symphony can be depicted in Figure 1. As illustrated in Figure 1, the Host and DUT are connected using a gateway router. Another detail spotted in the figure is an entity called "LOGIC" and "CALLBACK" both clarified later in this sentence. Logic constitutes hardware responsible for performing a hard reset on the DUT system. Callback, if we overuse the original terminology, it can be called a "driver". This callback instructs Symphony to perform a hard reset, when necessary, using the so-called "LOGIC" hardware in between. The driver (a.k.a. callback) is user-defined and varies between implementations. 

## Device Under Test
![Figure 2](docs/figs/result_message.png)
As depicted in Figure 2, the DUT is located inside the experiment room. This device is responsible for executing any command requested from the Host. Another task is to send back, through the network infrastructure, the results of the executed commands. The message that contains the result is in a specified dictionary format, shown in Figure 2.

## Getting started 
To install Symphony, follow these steps: Clone the repository and navigate to the symphony directory:
``git clone git@github.com:unipieslab/symphony.git
cd symphony``

Next, depending on your Linux package manager, execute the appropriate script:
For RedHat-based Linux, run:
``chmod +x install-Python<VERSION>_dnf.sh
./install-Python<VERSION>_dnf.sh``

For Debian-based Linux, run:
``chmod +x install-Python<VERSION>_apt.sh
./install-Python<VERSION>_apt.sh``

Once these steps are successfully completed, Symphony and all its dependencies will be installed. Lastly, to prepare the environment for Symphony to run, navigate to the following directory:
``cd host``

Then, execute the following command:
``make``

After completing this command, the host component of Symphony’s client- server architecture can be started by executing the following script:
``./runHost.sh``

It will then immediately attempt to connect to the DUT, if the component is up and running.

In folder docs you can find information about the internal functions of Symphony and their usage.
