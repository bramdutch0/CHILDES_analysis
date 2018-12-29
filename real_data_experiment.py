'''
real_data_experiment
This file tests a set of learners on data from a longitudinal 
study from the CHILDES database and calculates F1, precision, and
recall for each learner by taking nonchild utterances as input to the 
learners and child data as tests where the constructions the child
knows are compared to the predicted constructions each learner knows.

To run this program, use "python real_data_experiment.py [Directory 
with data in it]." The directory should contain files with preparsed data of the form
*[speaker]: [Utterance]
%gra: [parse of sentence]
And should use "CHI" to indicate the child is speaking

A list of learners is set up in the main() function. This list can be altered.
Documentation on the parameters for different learners can be found in 
Learner.py

The output of this program is stored in "results/real_data/[Directory with 
data in it]/". Output includes precision, recall, and F1 files which contain
the respective values at each test point as well as average_precision, average_recall,
and average_F1 that averages for each learner over all test points.

'''


import Extract_data
import Helper
import Learner
import numpy as np
import pandas as pd 
import os
import operator
import sys

DATA_DIR = "Sachs"
OUTPUT_DIRECTORY = "results/real_experiments/"

'''
Statistical Functions (includes get_TP, get_FP, get_FN)

	purpose: find the true positive, false positive, and false negative respectively
	inputs: true_list is a list that contains constructions the child actually knows 
			pred_list is a list that contains the constructions that the learner
				predicts the child should known_const_num
	outputs: return the TP, FP, FN respectively 	
'''
def get_TP(true_list, pred_list):
	TP = []
	for construction in true_list:
		if (construction in pred_list):
			TP.append(construction)
	return TP

def get_FP(true_list, pred_list):
	FP = []
	for construction in pred_list:
		if (construction not in true_list):
			FP.append(construction)
	return FP

def get_FN(true_list, pred_list):
	FN = []
	for construction in true_list:
		if (construction not in pred_list):
			FN.append(construction)
	return FN

'''
run real experiments 

	purpose: runs experiments to compare the learners to the actual learning of
				a child on a real dataset
	inputs: speech_data is a SpeechData object that contains the utterances from
				the corpus in the order they appear
			learners is a list of Learner objects to simulate 
			directory is the filepath to where the output files should be created
	outputs:creates 3 files:
				1) Recall.csv- lists the recalls of the learners at every 
					occurence of a child utterance
				2) Precision.csv- lists the precisions of the learners at every 
					occurence of a child utterance
				3) F1.csv- lists the F1 scores of the learners at every 
					occurence of a child utterance
				all of these files contain a header with the name of the learner
					and then each line contains the corresponding metric for a
					single occurrence of a child utterance
'''
def run_real_experiments(speech_data, learners, directory):
	#########################################################
	# 			SIMULATE CHILD LEARNING AND COMPARE
	#########################################################
	#keep track of constructions the child has used, which we will assume
	#are the only known constructions
	child_construction = []
	#also keep track of the known constructions of the learners and the child
	#at the time a child utterance is made
	known_constructions = []
	#keep track of true positive, false positive, and false negative
	#TP[i][learner] is the TP of learner at the ith child utterance
	TP = []
	FP = []
	FN = []
	#also keep track of recall, precision, and f1
	#recall[i][learner] is the recall of learner at the ith child utterance
	recall = []
	precision = []
	f1 = []
	#store all files in order
	files = os.listdir(DATA_DIR)
	files.sort()
	cha_files = []
	for filename in files:
			#ignore files that are not .cha files
			if (".cha" in filename):
				cha_files.append(filename)
	cha_files.sort()

	#increment every time a child construction is seen to keep track of 
	#position in all of the lists
	known_const_num = 0

	for infile in cha_files:
		filename = DATA_DIR + infile
		#print(filename)
		speech_data.add_file(filename)
		#feed in utterances in order
		#keep track of the number of instances in known_constructions
		for i in range(len(speech_data.get_utterances_in_order())):
			#print("%s/%s" % (i, len(speech_data.get_utterances_in_order())))
			utterance = speech_data.get_utterances_in_order()[i]
			print("%s: %s (%s)" % (utterance.get_speaker(), utterance.get_text()[:], utterance.get_verb_construction()))
			#if parent utterance, show to learners
			if (utterance.get_speaker() != "CHI"):
				for learner in learners:
					learners[learner].take_input(utterance.get_verb_construction())
			
			#if child utterance, update child_construction and update lists
			else:
				curr_const = utterance.get_verb_construction()
				if (curr_const not in child_construction):
					child_construction.append(curr_const)
				known_constructions.append({})
				TP.append({})
				FP.append({})
				FN.append({})
				recall.append({})
				precision.append({})
				f1.append({})
				known_constructions[known_const_num]["child"] = child_construction
				for learner in learners:
					known_constructions[known_const_num][learner] = learners[learner].get_known()
					curr_TP = get_TP(child_construction, learners[learner].get_known())
					curr_FP = get_FP(child_construction, learners[learner].get_known())
					curr_FN = get_FN(child_construction, learners[learner].get_known())
					TP[known_const_num][learner] = curr_TP
					FP[known_const_num][learner] = curr_FP
					FN[known_const_num][learner] = curr_FN
					
					#take care of case of division by 0. 
					#recall (TP + FN can't be 0, so don't worry about that case)
					recall[known_const_num][learner] = float(len(curr_TP))/(len(curr_TP) + len(curr_FN))
					#precision (if failed, set to 1)
					try:
						precision[known_const_num][learner] = float(len(curr_TP))/(len(curr_TP) + len(curr_FP))
					except:
						precision[known_const_num][learner] = 1
					#f1 (if failed, set to 0)
					try:
						f1[known_const_num][learner] = 2/((1/recall[known_const_num][learner]) + (1/precision[known_const_num][learner]))
					except:
						f1[known_const_num][learner] = 0 
					
					
					
				known_const_num += 1
		speech_data.clear()



	##############################################
	#			Write to output files
	##############################################
	recall_file = directory + "recall.csv"
	precision_file = directory + "precision.csv"
	f1_file = directory + "f1.csv"

	#recall
	with open(recall_file, "w+") as outfile:
		first_line = ""
		for learner in learners:
			first_line += learner + ", "
		outfile.write(first_line + "\n")
		#print(len(known_constructions))
		for i in range(len(known_constructions)):
			#print(i)
			curr_line = ""
			for learner in learners:
				curr_line += "%s, " % str(recall[i][learner])
			curr_line += "\n"
			outfile.write(curr_line)


	#precision
	with open(precision_file, "w+") as outfile:
		first_line = ""
		for learner in learners:
			first_line += learner + ", "
		outfile.write(first_line + "\n")
		for i in range(len(known_constructions)):
			curr_line = ""
			for learner in learners:
				curr_line += "%s, " % str(precision[i][learner])
			curr_line += "\n"
			outfile.write(curr_line)

	#f1
	with open(f1_file, "w+") as outfile:
		first_line = ""
		for learner in learners:
			first_line += learner + ", "
		outfile.write(first_line + "\n")
		for i in range(len(known_constructions)):
			curr_line = ""
			for learner in learners:
				curr_line += "%s, " % str(f1[i][learner])
			curr_line += "\n"
			outfile.write(curr_line)


'''
Consolidate results

	purpose: Takes the files created by run_real_experiments and averages the
				scores for each learner to find the overall recall, precision,
				and f1.
	inputs: directory is the filepath where the files are stored and where the
				output should be placed
	outputs: Creates 3 files:
				1) average_recall.csv
				2) average_precision.csv
				3) average_f1.csv
				each of these files contains a header with the names of the learners
					and then a single line containing the average scores for the
					corresponding metric
'''
def consolidate_results(directory):
	recall_file = directory + "recall.csv"
	precision_file = directory + "precision.csv"
	f1_file = directory + "f1.csv"

	########################
	#		recall
	########################
	df = pd.read_csv(recall_file)
	df = df.drop(labels=" ", axis=1)
	#total_recall stores an incremental counter for recall scores for each learner. 
	total_recall = {}
	for learner in df.keys():
		total_recall[learner] = 0.0
	#num_measurements is a counter for the number of measurements
	num_measurements = 0
	for i in range(len(df.keys()[0])):
		num_measurements += 1
		for learner in df.keys():
			total_recall[learner] += df[learner][i]
	for learner in total_recall.keys():
		total_recall[learner] = total_recall[learner] / num_measurements
	#write to file
	outfile_name = directory + "average_recall.csv"
	with open(outfile_name, "w+") as outfile:
		first_line = ""
		for key, value in sorted(total_recall.iteritems(), key=lambda (k,v): (v, k)):
			first_line += "%s, " % key
		outfile.write(first_line + "\n")
		data_line = ""
		for key, value in sorted(total_recall.iteritems(), key=lambda (k,v): (v, k)):
			data_line += "%s, " % str(value)
		outfile.write(data_line + "\n")

	#############################
	#		Precision
	#############################
	df = pd.read_csv(precision_file)
	df = df.drop(labels=" ", axis=1)
	#total_recall stores an incremental counter for recall scores for each learner. 
	total_precision = {}
	for learner in df.keys():
		total_precision[learner] = 0.0
	#num_measurements is a counter for the number of measurements
	num_measurements = 0
	for i in range(len(df.keys()[0])):
		num_measurements += 1
		for learner in df.keys():
			total_precision[learner] += df[learner][i]
	for learner in total_precision.keys():
		total_precision[learner] = total_precision[learner] / num_measurements
	#write to file
	outfile_name = directory + "average_precision.csv"
	with open(outfile_name, "w+") as outfile:
		first_line = ""
		for key, value in sorted(total_precision.iteritems(), key=lambda (k,v): (v, k)):
			first_line += "%s, " % key
		outfile.write(first_line + "\n")
		data_line = ""
		for key, value in sorted(total_precision.iteritems(), key=lambda (k,v): (v, k)):
			data_line += "%s, " % str(value)
		outfile.write(data_line + "\n")

	#################################
	#				F1
	#################################
	df = pd.read_csv(f1_file)
	df = df.drop(labels=" ", axis=1)
	#total_recall stores an incremental counter for recall scores for each learner. 
	total_f1 = {}
	for learner in df.keys():
		total_f1[learner] = 0.0
	#num_measurements is a counter for the number of measurements
	num_measurements = 0
	for i in range(len(df.keys()[0])):
		num_measurements += 1
		for learner in df.keys():
			total_f1[learner] += df[learner][i]
	for learner in total_f1.keys():
		total_f1[learner] = total_f1[learner] / num_measurements
	#write to file
	outfile_name = directory + "average_f1.csv"
	with open(outfile_name, "w+") as outfile:
		first_line = ""
		for key, value in sorted(total_f1.iteritems(), key=lambda (k,v): (v, k)):
			first_line += "%s, " % key
		outfile.write(first_line + "\n")
		data_line = ""
		for key, value in sorted(total_f1.iteritems(), key=lambda (k,v): (v, k)):
			data_line += "%s, " % str(value)
		outfile.write(data_line + "\n")

def main():
	###############################################################
	#	get constructions and data_distribution from speech data
	###############################################################
	#print("Extracting data")
	speech_data = Extract_data.SpeechData()
	#speech_data.add_from_dir(DATA_DIR)


	###################################################
	#			MAKE SURE DIRECTORY EXISTS
	###################################################
	if not os.path.exists(OUTPUT_DIRECTORY):
		os.makedirs(OUTPUT_DIRECTORY)
		print("making directory '%s'" % OUTPUT_DIRECTORY)


	######################################
	#			set up learners
	######################################
	print("Setting up Learners")
	learners = {}

	#frequentist
	learners["frequentist_1"] = Learner.FrequentistLearner(learn_times=1)
	learners["frequentist_2"] = Learner.FrequentistLearner(learn_times=2)
	learners["frequentist_3"] = Learner.FrequentistLearner(learn_times=3)
	learners["frequentist_5"] = Learner.FrequentistLearner(learn_times=5)
	learners["frequentist_10"] = Learner.FrequentistLearner(learn_times=10)
	learners["frequentist_15"] = Learner.FrequentistLearner(learn_times=15)
	#Complexity-Based
	learners["ComplexityBased_1"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:1})
	learners["ComplexityBased_09_1"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.9})
	learners["ComplexityBased_09_2"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.9, 2.0:0.8})
	learners["ComplexityBased_09_3"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.9, 2.0:0.7})
	learners["ComplexityBased_09_4"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.9, 2.0:0.6})
	learners["ComplexityBased_09_5"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.9, 2.0:0.5})
	learners["ComplexityBased_09_6"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.9, 2.0:0.4})
	learners["ComplexityBased_09_7"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.9, 2.0:0.4, 3.0:0.2})
	learners["ComplexityBased_09_8"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.9, 2.0:0.4, 2.5: 0.2, 3.0:0.1})
	learners["ComplexityBased_09_9"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.9, 2.0:0.4, 2.5: 0.1, 3.0:0.05})
	learners["ComplexityBased_08_1"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.8})
	learners["ComplexityBased_08_2"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.8, 2.0:0.7})
	learners["ComplexityBased_08_3"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.8, 2.0:0.6})
	learners["ComplexityBased_08_4"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.8, 2.0:0.5})
	learners["ComplexityBased_08_5"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.8, 2.0:0.4})
	learners["ComplexityBased_08_6"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.8, 2.0:0.4, 3.0:0.2})
	learners["ComplexityBased_08_7"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.8, 2.0:0.4, 2.5: 0.2, 3.0:0.1})
	learners["ComplexityBased_08_8"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.8, 2.0:0.4, 2.5: 0.1, 3.0:0.05})
	learners["ComplexityBased_07_1"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.7})
	learners["ComplexityBased_07_2"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.7, 2.0:0.6})
	learners["ComplexityBased_07_3"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.7, 2.0:0.5})
	learners["ComplexityBased_07_4"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.7, 2.0:0.4})
	learners["ComplexityBased_07_5"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.7, 2.0:0.4, 3.0:0.2})
	learners["ComplexityBased_07_6"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.7, 2.0:0.4, 2.5: 0.2, 3.0:0.1})
	learners["ComplexityBased_07_7"] = Learner.ComplexityBasedLearner(probability_dict={0.5: 1, 1.0:0.7, 2.0:0.4, 2.5: 0.1, 3.0:0.05})
	#Threshold
	learners["Threshold_10_10"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:10})
	learners["Threshold_10_8_1"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:8})
	learners["Threshold_10_8_2"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:8, 1.5:7, 2.0:6})
	learners["Threshold_10_8_"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:8, 1.5:7, 2.0:6, 3.0:4})
	learners["Threshold_10_8_3"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:8, 1.5:7, 2.0:6, 2.5: 4, 3.0: 2})
	learners["Threshold_10_8_4"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:8, 1.5:7, 2.0:6, 2.5: 4, 3.0: 2})
	learners["Threshold_10_8_5"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:8, 1.5:7, 2.0:6, 2.5: 4, 3.0: 1})
	learners["Threshold_10_8_6"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:8, 1.5:7, 2.0:6, 2.5: 4})
	learners["Threshold_10_8_7"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:8, 1.5:7, 2.0:6, 2.5: 3, 3.0: 2})
	learners["Threshold_10_8_8"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:8, 1.5:7, 2.0:6, 2.5: 3, 3.0: 1})
	learners["Threshold_10_8_9"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:8, 1.5:7, 2.0:6, 2.5: 3})
	learners["Threshold_10_8_10"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:8, 1.5:7, 2.0:6, 2.5: 1})
	learners["Threshold_10_6_1"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:6})
	learners["Threshold_10_6_2"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:6, 1.5: 5, 2.0: 4})
	learners["Threshold_10_6_3"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:6, 1.5: 4, 2.0: 2})
	learners["Threshold_10_6_4"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:6, 1.5:4, 2.0: 2, 2.5: 1})
	learners["Threshold_10_6_5"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:6, 1.5:4, 2.0: 1})
	learners["Threshold_10_6_6"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:6, 1.5:2, 2.0: 1})
	learners["Threshold_10_6_7"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:6, 1.5:3, 2.0: 2})
	learners["Threshold_10_6_8"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:6, 1.5:2, 2.0: 1})
	learners["Threshold_10_4_1"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:4, 1.5:3, 2.0: 2})
	learners["Threshold_10_4_2"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:4, 1.5:2, 2.0: 1})
	learners["Threshold_10_2"] = Learner.ThresholdLearner(complexity_dict={0.5: 10, 1.0:2, 1.5:1})
	learners["Threshold_8_6_1"] = Learner.ThresholdLearner(complexity_dict={0.5: 8, 1.0:6})
	learners["Threshold_8_6_2"] = Learner.ThresholdLearner(complexity_dict={0.5: 8, 1.0:6, 1.5: 5, 2.0: 4})
	learners["Threshold_8_6_3"] = Learner.ThresholdLearner(complexity_dict={0.5: 8, 1.0:6, 1.5: 4, 2.0: 2})
	learners["Threshold_8_6_4"] = Learner.ThresholdLearner(complexity_dict={0.5: 8, 1.0:6, 1.5:4, 2.0: 2, 2.5: 1})
	learners["Threshold_8_6_5"] = Learner.ThresholdLearner(complexity_dict={0.5: 8, 1.0:6, 1.5:4, 2.0: 1})
	learners["Threshold_8_6_6"] = Learner.ThresholdLearner(complexity_dict={0.5: 8, 1.0:6, 1.5:2, 2.0: 1})
	learners["Threshold_8_6_7"] = Learner.ThresholdLearner(complexity_dict={0.5: 8, 1.0:6, 1.5:3, 2.0: 2})
	learners["Threshold_8_6_8"] = Learner.ThresholdLearner(complexity_dict={0.5: 8, 1.0:6, 1.5:2, 2.0: 1})
	learners["Threshold_8_4_1"] = Learner.ThresholdLearner(complexity_dict={0.5: 8, 1.0:4, 1.5:3, 2.0: 2})
	learners["Threshold_8_4_2"] = Learner.ThresholdLearner(complexity_dict={0.5: 8, 1.0:4, 1.5:2, 2.0: 1})
	learners["Threshold_8_2"] = Learner.ThresholdLearner(complexity_dict={0.5: 8, 1.0:2, 1.5:1})
	learners["Threshold_6_4_1"] = Learner.ThresholdLearner(complexity_dict={0.5: 6, 1.0:4, 1.5:3, 2.0: 2})
	learners["Threshold_6_4_2"] = Learner.ThresholdLearner(complexity_dict={0.5: 6, 1.0:4, 1.5:2, 2.0: 1})
	learners["Threshold_6_2"] = Learner.ThresholdLearner(complexity_dict={0.5: 6, 1.0:2, 1.5:1})

	run_real_experiments(speech_data, learners, OUTPUT_DIRECTORY)
	consolidate_results(OUTPUT_DIRECTORY)

if __name__ == "__main__":
	DATA_DIR = sys.argv[1];
	#make sure DATA_DIR ends with "/"
	if (DATA_DIR[-1] != "/"):
		DATA_DIR += "/"
	OUTPUT_DIRECTORY = "results/real_data/" + DATA_DIR
	main()