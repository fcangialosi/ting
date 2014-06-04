cd tor
tar -zxvf tor-0.2.3.25-patched
cd tor-0.2.3.25-patched
yes | sudo yum install libevent-devel
yes | sudo yum install openssl
yes | sudo yum install openssl-devel
./configure
sudo make
sudo make install
