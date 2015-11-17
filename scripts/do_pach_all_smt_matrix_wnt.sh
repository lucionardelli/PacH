#!/bin/sh
# Hay que hacerlo lindo a esto. Por ahora, totalmente AD-HOC
printf '\n\n> SMT MATRIX CON INFORMACION NEGATIVA <'
date

# Sin poyección ni sampling
echo '> Comienza Sin proyec ni sampling'
echo '> Comienza DriversLicense.xes'
../src/pach.py ../../xes_logs/DriversLicense.xes --smt-matrix 300  --negative ../../negative_logs/DriversLicense.negatives.xes
echo '> Comienza choice.xes'
../src/pach.py ../../xes_logs/choice.xes --smt-matrix 300  --negative ../../negative_logs/choice.negatives.xes
echo '> Comienza confDimBlocking.xes'
../src/pach.py ../../xes_logs/confDimBlocking.xes --smt-matrix 300  --negative ../../negative_logs/confDimBlocking.negatives.xes
echo '> Comienza confDimStacked.xes'
../src/pach.py ../../xes_logs/confDimStacked.xes --smt-matrix 300  --negative ../../negative_logs/confDimStacked.negatives.xes

# Con poyección y/o sampling
echo ''
echo '> Comienza Con proyec y/o sampling'
echo '> Comienza incident.xes'
../src/pach.py ../../xes_logs/incident.xes --projection --smt-matrix 300  --negative ../../negative_logs/incident.negatives.xes
echo '> Comienza svn.xes'
../src/pach.py ../../xes_logs/svn.xes --projection --smt-matrix 300  --negative ../../negative_logs/svn.negatives.xes
echo '> Comienza FHMexampleN5.enc.xes'
../src/pach.py ../../xes_logs/FHMexampleN5.enc.xes --projection --smt-matrix 300  --negative ../../negative_logs/FHMexampleN5.enc.negatives.xes
echo '> Comienza receipt.xes'
../src/pach.py ../../xes_logs/receipt.xes --projection --smt-matrix 300  --negative ../../negative_logs/receipt.negatives.xes
echo '> Comienza documentflow.xes'
../src/pach.py ../../xes_logs/documentflow.xes --projection --smt-matrix 300  --negative ../../negative_logs/documentflow.negatives.xes
echo '> Comienza a32.xes'
../src/pach.py ../../xes_logs/a32.xes --projection 8 --smt-matrix 300  --negative ../../negative_logs/a32.negatives.xes
echo '> Comienza cycles5_2.xes'
../src/pach.py ../../xes_logs/cycles5_2.xes --projection --smt-matrix 300  --negative ../../negative_logs/cycles5_2.negatives.xes
echo '> Comienza DatabaseWithMutex-PT-02.xes'
../src/pach.py ../../xes_logs/DatabaseWithMutex-PT-02.xes --projection --smt-matrix 300  --negative ../../negative_logs/DatabaseWithMutex-PT-02.negatives.xes
echo '> Comienza t32.xes'
../src/pach.py ../../xes_logs/t32.xes --projection 10  --smt-matrix 300  --negative ../../negative_logs/t32.negatives.xes
echo '> Comienza a42.xes'
../src/pach.py ../../xes_logs/a42.xes --projection 10 --smt-matrix 300  --negative ../../negative_logs/a42.negatives.xes
echo '> Comienza telecom.xes'
../src/pach.py ../../xes_logs/telecom.xes --projection --smt-matrix 300  --negative ../../negative_logs/telecom.negatives.xes
echo '> Comienza complex.enc.xes'
../src/pach.py ../../xes_logs/complex.enc.xes --projection 8 --smt-matrix 300  --negative ../../negative_logs/complex.enc.negatives.xes
mv ./*.pnml ../../pnml/smt_matrix/negatives/
mv ./*.out ../../statistics/smt_matrix/negatives/
