#!/bin/sh
# Hay que hacerlo lindo a esto. Por ahora, totalmente AD-HOC
printf '\n\n> SMT MATRIX <'

# Sin poyección ni sampling
echo '> Comienza Sin proyec ni sampling'
echo '> Comienza choice.xes'
../src/pach.py ../../xes_logs/choice.xes --smt-matrix 300
echo '> Comienza confDimBlocking.xes'
../src/pach.py ../../xes_logs/confDimBlocking.xes --smt-matrix 300
echo '> Comienza DriversLicense.xes'
../src/pach.py ../../xes_logs/DriversLicense.xes --smt-matrix 300
echo '> Comienza confDimStacked.xes'
../src/pach.py ../../xes_logs/confDimStacked.xes --smt-matrix 300

# Con poyección y/o sampling
echo ''
echo '> Comienza Con proyec y/o sampling'
echo '> Comienza log1.xes'
../src/pach.py ../../xes_logs/log1.xes --projection 11 --smt-matrix 300
echo '> Comienza a32.xes'
../src/pach.py ../../xes_logs/a32.xes --projection 8 --smt-matrix 300
echo '> Comienza DatabaseWithMutex-PT-02.xes'
../src/pach.py ../../xes_logs/DatabaseWithMutex-PT-02.xes --projection --smt-matrix 300
echo '> Comienza cycles5_2.xes'
../src/pach.py ../../xes_logs/cycles5_2.xes --projection --smt-matrix 300
echo '> Comienza a42.xes'
../src/pach.py ../../xes_logs/a42.xes --projection 10 --smt-matrix 300
echo '> Comienza t32.xes'
../src/pach.py ../../xes_logs/t32.xes --projection --smt-matrix 300
echo '> Comienza Peterson-PT-2.xes'
../src/pach.py ../../xes_logs/Peterson-PT-2.xes --projection 10 --smt-matrix 300
echo '> Comienza telecom.xes'
../src/pach.py ../../xes_logs/telecom.xes --projection --smt-matrix 300
echo '> Comienza complex.enc.xes'
../src/pach.py ../../xes_logs/complex.enc.xes --projection 8 --smt-matrix 300
echo '> Comienza documentflow.xes'
../src/pach.py ../../xes_logs/documentflow.xes --projection --smt-matrix 300
echo '> Comienza FHMexampleN5.enc.xes'
../src/pach.py ../../xes_logs/FHMexampleN5.enc.xes --projection --smt-matrix 300
echo '> Comienza incident.xes'
../src/pach.py ../../xes_logs/incident.xes --projection --smt-matrix 300
echo '> Comienza receipt.xes'
../src/pach.py ../../xes_logs/receipt.xes --projection --smt-matrix 300
echo '> Comienza svn.xes'
../src/pach.py ../../xes_logs/svn.xes --projection --smt-matrix 300
mv ./*.pnml ../../pnml/smt_matrix/
mv ./*.out ../../statistics/smt_matrix/
