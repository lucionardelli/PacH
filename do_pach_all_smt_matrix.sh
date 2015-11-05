#!/bin/sh
# Hay que hacerlo lindo a esto. Por ahora, totalmente AD-HOC

# Sin poyección ni sampling
echo '> Comienza Sin proyec ni sampling'
echo '> Comienza illustrative_example.xes'
./pach.py ../xes_logs/illustrative_example.xes  --verbose --smt-simp
echo '> Comienza running-example-just-two-cases.xes'
./pach.py ../xes_logs/running-example-just-two-cases.xes  --verbose --smt-simp
echo '> Comienza choice.xes'
./pach.py ../xes_logs/choice.xes  --verbose --smt-simp
echo '> Comienza confDimBlocking.xes'
./pach.py ../xes_logs/confDimBlocking.xes  --verbose --smt-simp
echo '> Comienza DriversLicense.xes'
./pach.py ../xes_logs/DriversLicense.xes  --verbose --smt-simp
echo '> Comienza confDimStacked.xes'
./pach.py ../xes_logs/confDimStacked.xes  --verbose --smt-simp

# Con poyección, sin sampling
echo ''
echo '> Comienza Con proyec, sin sampling'
echo '> Comienza log1.xes'
# Con valores de projection mayor, no anda
./pach.py ../xes_logs/log1.xes --projection 11 --smt-simp
echo '> Comienza a32.xes'
./pach.py ../xes_logs/a32.xes --projection --smt-simp
#echo '> Comienza Angiogenesis-PT-01.xes'
#./pach.py ../xes_logs/Angiogenesis-PT-01.xes --projection 8 --sampling 3 100
echo '> Comienza DatabaseWithMutex-PT-02.xes'
./pach.py ../xes_logs/DatabaseWithMutex-PT-02.xes --projection --smt-simp
echo '> Comienza cycles5_2.xes'
./pach.py ../xes_logs/cycles5_2.xes --projection --smt-simp
echo '> Comienza a42.xes'
./pach.py ../xes_logs/a42.xes --projection --smt-simp
echo '> Comienza t32.xes'
./pach.py ../xes_logs/t32.xes --projection --smt-simp
echo '> Comienza Peterson-PT-2.xes'
./pach.py ../xes_logs/Peterson-PT-2.xes --projection --smt-simp
echo '> Comienza telecom.xes'
./pach.py ../xes_logs/telecom.xes --projection --smt-simp
echo '> Comienza complex.enc.xes'
./pach.py ../xes_logs/complex.enc.xes --projection --smt-simp
echo '> Comienza documentflow.xes'
./pach.py ../xes_logs/documentflow.xes --projection --smt-simp
echo '> Comienza FHMexampleN5.enc.xes'
./pach.py ../xes_logs/FHMexampleN5.enc.xes --projection --smt-simp
echo '> Comienza incident.xes'
./pach.py ../xes_logs/incident.xes --projection --smt-simp
echo '> Comienza receipt.xes'
./pach.py ../xes_logs/receipt.xes --projection --smt-simp
echo '> Comienza svn.xes'
./pach.py ../xes_logs/svn.xes --projection --smt-simp
mv ../xes_logs/*.pnml ../pnml/smt_matrix/
