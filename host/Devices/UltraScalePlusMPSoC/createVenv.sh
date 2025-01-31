pip3 install virtualenv
python3 -m venv ./venv 
source venv/bin/activate
venv/bin/python3 -m pip install --upgrade pip
pip3 install rpyc pyserial esptool orjson requests cloudpickle
