#!/bin/sh
# Hay que hacerlo lindo a esto. Por ahora, totalmente AD-HOC
printf '\n\n> SIN SMT CON TRAZAS NEGATIVAS<'

# Sin poyección ni sampling
echo '> Comienza Sin proyec ni sampling'
echo '> Comienza DriversLicense.xes'
./pach.py ../xes_logs/DriversLicense.xes --negative ../negative_logs/DriversLicense.negatives.xes
echo '> Comienza choice.xes'
./pach.py ../xes_logs/choice.xes --negative ../negative_logs/choice.negatives.xes
echo '> Comienza confDimBlocking.xes'
./pach.py ../xes_logs/confDimBlocking.xes --negative ../negative_logs/confDimBlocking.negatives.xes
echo '> Comienza confDimStacked.xes'
./pach.py ../xes_logs/confDimStacked.xes --negative ../negative_logs/confDimStacked.negatives.xes

# Con poyección y/o sampling
echo ''
echo '> Comienza Con proyec y/o sampling'
echo '> Comienza incident.xes'
./pach.py ../xes_logs/incident.xes --projection --negative ../negative_logs/incident.negatives.xes
echo '> Comienza svn.xes'
./pach.py ../xes_logs/svn.xes --projection --negative ../negative_logs/svn.negatives.xes
echo '> Comienza FHMexampleN5.enc.xes'
./pach.py ../xes_logs/FHMexampleN5.enc.xes --projection --negative ../negative_logs/FHMexampleN5.enc.negatives.xes
echo '> Comienza receipt.xes'
./pach.py ../xes_logs/receipt.xes --projection --negative ../negative_logs/receipt.negatives.xes
echo '> Comienza documentflow.xes'
./pach.py ../xes_logs/documentflow.xes --projection --negative ../negative_logs/documentflow.negatives.xes
echo '> Comienza a32.xes'
./pach.py ../xes_logs/a32.xes --projection 8 --negative ../negative_logs/a32.negatives.xes
echo '> Comienza cycles5_2.xes'
./pach.py ../xes_logs/cycles5_2.xes --projection --negative ../negative_logs/cycles5_2.negatives.xes
echo '> Comienza DatabaseWithMutex-PT-02.xes'
./pach.py ../xes_logs/DatabaseWithMutex-PT-02.xes --projection --negative ../negative_logs/DatabaseWithMutex-PT-02.negatives.xes
echo '> Comienza t32.xes'
./pach.py ../xes_logs/t32.xes --projection 10  --negative ../negative_logs/t32.negatives.xes
#Trazas negativas muy grandes, no pueden siquiera parsearse
#echo '> Comienza a42.xes'
#./pach.py ../xes_logs/a42.xes --projection 10 --negative ../negative_logs/a42.negatives.xes
#echo '> Comienza telecom.xes'
#./pach.py ../xes_logs/telecom.xes --projection --negative ../negative_logs/telecom.negatives.xes
#echo '> Comienza complex.enc.xes'
#./pach.py ../xes_logs/complex.enc.xes --projection 8 --negative ../negative_logs/complex.enc.negatives.xes
mv ./*.pnml ../pnml/no_smt/negatives/
mv ./*.out ../statistics/no_smt/negatives/
