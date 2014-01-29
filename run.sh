#!/bin/bash

echo "Creating 3 Ting Servers..."

nohup python ting_server.py > server_nohup.out &
nohup python ting_server2.py > server2_nohup.out &
nohup python ting_server3.py > server3_nohup.out &

echo "Server setup complete."
echo "Creating 3 Ting Clients..." 

nohup python ting_client2.py verify -v -dp 8080 -nt 100 -np 1000 -sp 9050 -cp 9051 -p d67b28212377617448a2ac192e11372ad951fd13 b0171148a7081858ee639b9451af4d6ce0f68361 > client1_nohup.out &
nohup python ting_client2.py verify -v -dp 8087 -nt 100 -np 1000 -sp 9250 -cp 9251 -p 9d4d995aa745a3caa6276afad505d3e4097aa075 b0171148a7081858ee639b9451af4d6ce0f68361 > client2_nohup.out &
nohup python ting_client2.py verify -v -dp 8088 -nt 100 -np 1000 -sp 9150 -cp 9151 -p a53c46f5b157dd83366d45a8e99a244934a14c46 d67b28212377617448a2ac192e11372ad951fd13 > client3_nohup.out &

echo "Clients now executing."

ps aux | grep ting
