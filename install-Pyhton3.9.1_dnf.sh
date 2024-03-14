sudo dnf update
sudo dnf groupinstall "Development Tools"
sudo dnf install zlib-devel.x86_64 ncurses-devel.i686 gdbm-devel.x86_64 nss-devel.x86_64 openssl-devel.x86_64 readline-devel.x86_64 libffi-devel.x86_64 libsqlite3x-devel.x86_64 bzip2-devel.x86_64
wget https://www.python.org/ftp/python/3.9.1/Python-3.9.1.tgz
tar -xf Python-3.9.1.tgz
cd Python-3.9.1
./configure --enable-optimizations
make -j 4
sudo make altinstall
python3.9 --version
