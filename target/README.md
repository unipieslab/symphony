## DUT

The DUT is a service running in the target that will capture any essential information for the experiment. It is designed to run in Linux hosts.

In order to setup Symphony, the dut.py need to run as a servive in the target.
The servie file is `rpyc.service` in the `services` directory.

> *Do not forget to adjust the `ExecStart` path in `rpyc.service` to match your installation folder in the target*

To do so, copy the service file in the systemd directory

> `cp services/rpyc.service /etc/systemd/system/`

and run the script 

> `./update_service.sh`


