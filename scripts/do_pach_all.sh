#!/bin/sh
# Hay que hacerlo lindo a esto. Por ahora, totalmente AD-HOC
printf '\n\n> SIN SMT <'

# Sin poyección ni sampling
echo '> Comienza Sin proyec ni sampling'
echo '> Comienza DriversLicense.xes'
../src/pach.py ../../xes_logs/DriversLicense.xes
echo '> Comienza choice.xes'
../src/pach.py ../../xes_logs/choice.xes
echo '> Comienza confDimBlocking.xes'
../src/pach.py ../../xes_logs/confDimBlocking.xes
echo '> Comienza confDimStacked.xes'
../src/pach.py ../../xes_logs/confDimStacked.xes

# Con poyección y/o sampling
echo ''
echo '> Comienza Con proyec y/o sampling'
echo '> Comienza incident.xes'
../src/pach.py ../../xes_logs/incident.xes --projection
echo '> Comienza svn.xes'
../src/pach.py ../../xes_logs/svn.xes --projection
echo '> Comienza FHMexampleN5.enc.xes'
../src/pach.py ../../xes_logs/FHMexampleN5.enc.xes --projection
echo '> Comienza receipt.xes'
../src/pach.py ../../xes_logs/receipt.xes --projection
echo '> Comienza documentflow.xes'
../src/pach.py ../../xes_logs/documentflow.xes --projection
echo '> Comienza a32.xes'
../src/pach.py ../../xes_logs/a32.xes --projection 8
echo '> Comienza cycles5_2.xes'
../src/pach.py ../../xes_logs/cycles5_2.xes --projection
echo '> Comienza DatabaseWithMutex-PT-02.xes'
../src/pach.py ../../xes_logs/DatabaseWithMutex-PT-02.xes --projection
echo '> Comienza t32.xes'
../src/pach.py ../../xes_logs/t32.xes --projection 10 
echo '> Comienza a42.xes'
../src/pach.py ../../xes_logs/a42.xes --projection 10
echo '> Comienza telecom.xes'
../src/pach.py ../../xes_logs/telecom.xes --projection
echo '> Comienza complex.enc.xes'
../src/pach.py ../../xes_logs/complex.enc.xes --projection 8 
mv ./*.pnml ../../pnml/no_smt/
mv ./*.out ../../statistics/no_smt/
