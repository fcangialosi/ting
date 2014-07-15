ID=$1
DP="666$ID"
CP="915$ID"
SP="905$ID"

until $(python test.py -i data/inputs/$2 -o data/outputs/$3 -id $ID -dp $DP -cp $CP -sp $SP >> logs/client_$ID.log); do
  echo "Client $ID crashed with exit code $?. (pid=$$) Respawning.."
  echo "Client $ID (ppid=$$) crashed with exit code $?, respawning.." | mailx -r "watchdog@bluepill.cs.umd.edu" "4103757977@vtext.com"
  tail -n 30 logs/client_$ID.log | mailx -r "watchdog@bluepill.cs.umd.edu" -s "Client $ID (ppid=$$) crashed with exit code $?" "fcangialosi94@gmail.com" 
  sleep 10
done
