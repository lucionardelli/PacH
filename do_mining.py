# verbose=False, samp_num=1, samp_size=None,
# proj_size=None, proj_connected=True, nfilename=None, max_coef=10,
# smt_matrix=False, smt_iter=False, smt_timeout=0, sanity_check=False
# Negative but no smt set -> removal only

from os.path import isfile
import os, shutil, sys, traceback

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + '/src')
from pach import PacH
from utils import check_argv, parse_config, parse_config_output

def clean_output(folder):
	for basename in os.listdir(folder):
		if not basename.endswith('.pnml') and not basename.endswith('.out'):
			continue
		print ' Cleaning: ', os.path.join(folder, basename)
		os.remove(os.path.join(folder, basename))

def move_output(name, folder):
	pwd = os.getcwd()
	for basename in os.listdir(pwd):
		if basename.endswith('.pnml'):
			pnml_file = os.path.join(pwd, basename)
			if os.path.isfile(pnml_file):
				shutil.copy2(pnml_file, folder + '/' + name + '.pnml')
				os.remove(pnml_file)
		elif basename.endswith('.out'):
			out_file = os.path.join(pwd, basename)
			if os.path.isfile(out_file):
				shutil.copy2(out_file, folder + '/' + name + '.out')
				os.remove(out_file)

MINE_ARGS = {	'choice':{},
		'confDimBlocking':{},
		'incident':{'proj_size' : 0},
		'svn':{'proj_size' : 0},
		'FHMexampleN5':{'proj_size' : 0},
		'FHMexampleN5.enc':{'proj_size' : 0},
		'receipt':{'proj_size' : 0},
		'documentflow':{'proj_size' : 0},
		'a32':{'proj_size' : 12},
		'cycles5_2':{'proj_size' : 0},
		'DatabaseWithMutex-PT-02':{'proj_size' : 0},
		't32':{'proj_size' : 12},
		'a42':{'proj_size' : 10},
		'telecom':{'proj_size' : 0},
		'complex.enc':{'proj_size' : 12},
		'complex':{'proj_size' : 12},
}

def add_iter(mine_args):
	for k in mine_args.keys():
		mine_args[k]['smt_matrix'] = False
		mine_args[k]['smt_iter'] = True
		mine_args[k]['smt_timeout'] = 1
	return mine_args

def add_matrix(mine_args):
	for k in mine_args.keys():
		mine_args[k]['smt_matrix'] = True
		mine_args[k]['smt_iter'] = False
		mine_args[k]['smt_timeout'] = 1
	return mine_args

def run_pach(filename, **arguments):
	pach = PacH(filename, **arguments)
	complexity = pach.pach()
	initial = pach.initial_complexity
	print " Done, complexity is:",initial,'to -->',complexity
	pach.generate_pnml()
	return (complexity, initial)


PWD = os.getcwd()
LOG_HOME = PWD + '/../Experiments/logs'
NEG_HOME = PWD + '/../Experiments/negativeLogs'
OUTPUT_HOME = PWD + '/../Experiments/models'
KFOLD_OUTPUT_HOME = PWD + '/../Experiments/kfold'
KFOLD_COLLAPSEDLOG_HOME = PWD + '/../Experiments/kfold/collapsedLogs'
KFOLDS = 10

def do_log(log_file, base_name, out_folder, moved_name = None):
	if moved_name is None: moved_name = base_name
	print "Mining:",base_name,moved_name
	print MINE_ARGS[base_name]
	ret = run_pach(log_file, **MINE_ARGS[base_name])
	move_output(moved_name, out_folder)
	return ret

def do_net(net_file, base_name, out_folder, moved_name = None, negative_log = None, check_purpose = False):
	if moved_name is None: moved_name = base_name
	print "Simplifying:",base_name,net_file,moved_name
	MINE_ARGS[base_name].pop('nfilename', None)
	if negative_log is not None:
		if not os.path.isfile(negative_log):
			print ' *** OOPS:   ' + negative_log
		if check_purpose and not 'complex' in net_file:
			print ' *** PURPOSE: going to check  '
			print MINE_ARGS[base_name]
			ret = run_pach(net_file, **MINE_ARGS[base_name])
			if ret[0] == ret[1]:
				print ' *** PURPOSE: no need to even try negative one  '
				move_output(moved_name, out_folder)
				return ret
		MINE_ARGS[base_name]['nfilename'] = negative_log
	print MINE_ARGS[base_name]
	ret = run_pach(net_file, **MINE_ARGS[base_name])
	move_output(moved_name, out_folder)
	return ret

#### ENTRY POINTS ####

print sys.argv
input_command = sys.argv[1]
miner_algos = [sys.argv[2]] if len(sys.argv) > 2 else os.listdir(OUTPUT_HOME + '/mining')

if input_command is None:
	pass

elif input_command == "kfold-neg-rem" or input_command == "kfold-neg-iter" or input_command == "kfold-neg-matrix" or \
	input_command == "kfold-iter" or input_command == "kfold-matrix":
	add_neg = input_command.startswith('kfold-neg-')
	input_command = input_command.replace('kfold-','').replace('neg-','')
	if input_command == "iter": add_iter(MINE_ARGS)
	if input_command == "matrix": add_matrix(MINE_ARGS)
	for algo in miner_algos:
		ins = KFOLD_OUTPUT_HOME + '/mining/' + algo
		if add_neg: out = KFOLD_OUTPUT_HOME + '/with_negatives/' + algo + '-' + input_command
		else: out = KFOLD_OUTPUT_HOME + '/without_negatives/' + algo + '-' + input_command
		print ins
		print out
		if not os.path.isdir(out):
			print ' *** skipping'
			continue
		clean_output(out)
		for basename in os.listdir(ins):
			if 'complex' in basename: continue # NO TIME
			if not basename.endswith('.pnml'): continue
			petriname = basename.replace('.pnml', '')
			print petriname
			negative_log = KFOLD_COLLAPSEDLOG_HOME + '/keep_' + petriname.replace('.pos', '.neg') + '.xes' if add_neg else None
			if negative_log and not os.path.isfile(negative_log):
				print ' *** OOPS NEGATIVE LOG:   ' + negative_log
				negative_log = negative_log.replace('.enc.', '.')
			basic = basename.split('.')[0].replace('allbut_', '')
			try:
				check_purpose = not input_command == "rem"
				do_net(ins + '/' + basename, basic, out, moved_name = petriname, negative_log = negative_log, check_purpose = check_purpose)
			except:
				clean_output(os.getcwd())
				print str(sys.exc_info()[0])
				exc_info = sys.exc_info()
				traceback.print_exception(*exc_info)
			
elif input_command == "kfold-mine":
	out = KFOLD_OUTPUT_HOME + '/mining/polyhedra'
	clean_output(out)
	for basename in os.listdir(LOG_HOME):
		if not basename.endswith('.xes'): continue
		logname = basename.replace('.xes', '')
		print logname
		for i in range(KFOLDS):
			collapsedlog = KFOLD_COLLAPSEDLOG_HOME + '/' + 'keep_allbut_'+logname+'.pos.'+str(i)+'.xes'
			collapsedlog = collapsedlog.replace('.enc.', '.')
			if not os.path.isfile(collapsedlog):
				print ' *** OOPS COLLAPSED LOG:   ' + collapsedlog
			newname = 'allbut_'+logname+'.pos.'+str(i)
			do_log(collapsedlog, logname, out, newname)

elif input_command == "mine":
	out = OUTPUT_HOME + '/mining/polyhedra'
	clean_output(out)
	for basename in os.listdir(LOG_HOME):
		if not basename.endswith('.xes'): continue
		do_log(LOG_HOME + '/' + basename, basename.replace('.xes', ''), out)

elif input_command == "neg-rem" or input_command == "neg-iter" or input_command == "neg-matrix" or \
	input_command == "iter" or input_command == "matrix":
	add_neg = input_command.startswith('neg-')
	input_command = input_command.replace('neg-','')
	if input_command == "iter": add_iter(MINE_ARGS)
	if input_command == "matrix": add_matrix(MINE_ARGS)
	for algo in miner_algos:
		ins = OUTPUT_HOME + '/mining/' + algo
		if add_neg: out = OUTPUT_HOME + '/with_negatives/' + algo + '-' + input_command
		else: out = OUTPUT_HOME + '/without_negatives/' + algo + '-' + input_command
		print out
		try: clean_output(out)
		except:
			print "Output dir does not exist", out
			continue
		for basename in os.listdir(ins):
			if not basename.endswith('.pnml'): continue
			negative_log = NEG_HOME + '/' + basename.replace('.pnml', '.xes') if add_neg else None
			if negative_log and not os.path.isfile(negative_log):
				print ' *** OOPS NEGATIVE LOG:   ' + negative_log
				negative_log = negative_log.replace('.enc.', '.')
			try:
				check_purpose = not input_command == "rem"
				do_net(ins + '/' + basename, basename.replace('.pnml', ''), out, negative_log = negative_log, check_purpose = check_purpose)
			except:
				clean_output(os.getcwd())
				exc_info = sys.exc_info()
				print str(exc_info[0])
				traceback.print_exception(*exc_info)

elif input_command == "neg-rem-after-iter":
	for algo in miner_algos:
		ins = OUTPUT_HOME + '/without_negatives/' + algo + '-iter'
		out = OUTPUT_HOME + '/with_negatives/' + algo + '-iter-rem'
		print out
		try: clean_output(out)
		except:
			print "  *** Output dir does not exist", out
			continue
		for basename in os.listdir(ins):
			if not basename.endswith('.pnml'): continue
			negative_log = NEG_HOME + '/' + basename.replace('.pnml', '.xes')
			if negative_log and not os.path.isfile(negative_log):
				print ' *** OOPS NEGATIVE LOG:   ' + negative_log
				negative_log = negative_log.replace('.enc.', '.')
			try:
				do_net(ins + '/' + basename, basename.replace('.pnml', ''), out, negative_log = negative_log, check_purpose = False)
			except:
				clean_output(os.getcwd())
				exc_info = sys.exc_info()
				print str(exc_info[0])
				traceback.print_exception(*exc_info)
				
elif input_command == "kfold-neg-rem-after-iter":
	for algo in miner_algos:
		ins = KFOLD_OUTPUT_HOME + '/without_negatives/' + algo + '-iter'
		out = KFOLD_OUTPUT_HOME + '/with_negatives/' + algo + '-iter-rem'
		print out
		try: clean_output(out)
		except:
			print "  *** Output dir does not exist", out
			continue
		for basename in os.listdir(ins):
			if 'complex' in basename: continue # NO TIME
			if not basename.endswith('.pnml'): continue
			petriname = basename.replace('.pnml', '')
			print petriname
			negative_log = KFOLD_COLLAPSEDLOG_HOME + '/keep_' + petriname.replace('.pos', '.neg') + '.xes'
			if negative_log and not os.path.isfile(negative_log):
				print ' *** OOPS NEGATIVE LOG:   ' + negative_log
				negative_log = negative_log.replace('.enc.', '.')
			basic = basename.split('.')[0].replace('allbut_', '')
			try:
				do_net(ins + '/' + basename, basic, out, moved_name = petriname, negative_log = negative_log, check_purpose = False)
			except:
				clean_output(os.getcwd())
				exc_info = sys.exc_info()
				print str(exc_info[0])
				traceback.print_exception(*exc_info)
				
	
