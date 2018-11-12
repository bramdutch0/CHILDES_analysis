'''
This file contains classes and functions to extract data into 
the form of grammatical relations (GR's) so that it can be processed
'''


import os
import operator
import math
import numpy as np
from collections import defaultdict, namedtuple



##################################################################
#
#				HELPER FUNCTIONS AND CLASSES
#
##################################################################
'''
Construction graph

	Stores a list of GR's in a graphical form
	Contains methods to find a path between two nodes
'''
class ConstructionGraph():
	def __init__(self, connections):
		self._graph = defaultdict(set)
		self.add_connections(connections)

	def add_connections(self, connections):
		for node1, node2 in connections:
			self.add(node1, node2)

	def add(self, node1, node2):
		self._graph[node1].add(node2)

	def find_path(self, node1, node2, path=[]):
		path = path + [node1]
		if node1 == node2:
			return path
		if node1 not in self._graph:
			return None
		for node in self._graph[node1]:
			if node not in path:
				new_path = self.find_path(node, node2, path)
				if new_path:
					return new_path
		return None


'''
Prune graph

	inputs: construction is a string of grammatical relations with 
	the form "edge_end|edge_beg|gr." 

	outputs: returns a modified construction that prunes any
	nodes that contain unwanted GR's or are not connected to 
	the ROOT node
'''
def prune_graph(construction):
	#CHILDES constructions that aren't involved in the verb construction
	remove_constructions = ['APP', 'CJCT', 'CMOD', 'COM', 
		'CONJ', 'COORD', 'DATE', 'DET', 'ENUM', 'JCT', 'LINK', 
		'MOD', 'NEG', 'NJCT', 'POSS', 'POSTMOD', 'PQ', 'PUNC', 
		'PUNCT', 'QUANT', 'XJCT', 'XMOD']

	#remove any GR's not related to verb construction
	for i in range(len(construction)):
		for const in remove_constructions:
			for word in construction:
				curr = word.split("|")
				try:
					if (const == curr[2]):
						construction.remove(word)
				except:
					pass

	connections = []
	for word in construction:
		word = word.split("|")
		connections.append([int(word[0]), int(word[1])])
	#construct graph
	graph = ConstructionGraph(connections)

	pruned = []
	for word in construction:
		curr = word.split("|")
		if (graph.find_path(int(curr[0]), 0)):
			pruned.append(word)

	return pruned







###################################################################
#
#
#				UTTERANCE CLASSES AND FUNCTIONS
#
###################################################################

'''
Parse for GR

	inputs: text is a string to be converted into GR's
	outpus: returns a string of GR's

	NOT IMPLEMENTED
'''
def parse_for_GR(text):
	return None


'''
Extract from Childes

	inputs: text is a childes utterance of the form:
		'*(SPEAKER):	Actual transcription of the utternace
		%mor: Not important 
		%gra:	Grammatical Construction for the transcription (should 
			be a list of grammatical relations of the form 
			"node_num|taget_node|GR")'

	outputs: returns the speaker, transciption, GR's
'''
def extract_from_childes(text):
	#print("extracting from '%s'" %text)

	lines = text.split('\n')
	#get spearker
	speaker = lines[0].split('\t')[0]
	speaker = speaker[1:-1]

	#get transcript
	transcript = lines[0].split('\t')[1]
	while("%" not in lines[1]):
		lines = lines[1:]
		transcript += " "
		transcript += lines[0].strip()

	#get GR's
	gr_text = ""
	found_gr = False
	for line in lines[1:]:
		if (found_gr):
			#make sure that the gr hasn't ended (signified by 
			#another %)
			if ("%" in line):
				found_gr = False
				break
			#keep appending the text to gr
			gr_text += " "
			gr_text += line.strip()
		elif ("%gra" in line):
			found_gr = True
			#don't append "%gra" to gr_text
			gr_text += line.split('\t')[1].strip()

	return speaker, transcript, gr_text


'''
Extract Childes utterances

	inputs: filename is the file to extract from. It is expected that
			this is a file from the CHILDES database which contains 
			speech data in the form:
				*(SPEAKER):	Actual transcription of the utternace
				%mor: Not important 
				%gra:	Grammatical Construction for the transcription 
				(should be a list of grammatical relations of the form 
				"node_num|taget_node|GR")

	outputs: returns a list of utterances in the file in order
'''
def extract_childes_utterances(filename):
	utterance_list = []
	with open(filename) as infile:
		lines = infile.readlines()
		i = 0
		found_utterances = False
		curr_text = ""
		while ("@End" not in lines[i]):
			#wait for first utterance
			if(not found_utterances):
				if (lines[i][0] == "*"):
					found_utterances = True
			if (found_utterances):
				#new utterance
				if (lines[i][0] == "*"):
					#if curr_utterance contains something, extract the 
					#utterance and start a new one
					if (curr_text != ""):
						try:
							utterance_list.append(ChildesUtterance(curr_text))
						#if it's not a well-formed utterance, ignore it
						except:
							pass
						curr_text = ""

				#add line to curr_utterance
				curr_text += lines[i]
			i += 1

		#extract last utterance
		try:
			utterance_list.append(ChildesUtterance(curr_text))
		#if it's not a well-formed utterance, ignore it
		except:
			pass
	return utterance_list


'''
well_formed

	inputs: construction is a list of GR's.
	outputs: returns True if the construction doesn't contain
			'INCROOT' and if the construction isn't 'None'
'''
def well_formed(construction):
	if (construction == None):
		return False
	elif ("INCROOT" in construction):
		return False
	return True



'''
Utterance

	Contains data on a generic utterance
	Constructor takes as input a sentence.
	The Grammatical Construction is extracted automatically

	Contains methods to extract the verb construction from the GR 
	construction 
'''
class Utterance:
	def __init__(self, text):
		self.text = text
		self.construction = parse_for_GR(text)

	'''
	Get verb construction

		outputs: returns a string of GR's that removes any GR's not related
		to the construction. Also converts node numbers into generic forms 
		(ie. "1|2|SUBJ 2|0|ROOT" becomes "n1|x|SUBJ x|0|ROOT")
	'''
	def get_verb_construction(self):
		construction = self.construction[:-1].split()

		try:
			construction = prune_graph(construction)
		except:
			return None

		#find root
		root = ""
		for word in construction:
			if ("ROOT" in word):
				root = word
				break
		#make sure there is a root
		if (root == ""):
			return None
		
		else:
			#map root position to 'x'
			mappings = {}
			mappings[int(root.split("|")[0])] = "x"
			#number nouns, verbs, auxes, and preds starting with 1
			#increment after using that number
			nouns = 1
			verbs = 1
			auxs = 1
			preds = 1
			
			

			inf = False
			for i in range(len(construction)):
				#replace numbers with placeholders
				curr = construction[i].split("|")
				
				for j in range(len(curr)):
					#subjects and objects
					if ("SUBJ" in curr[j] or "OBJ" in curr[j]):
						mappings[int(curr[0])] = "n" + str(nouns)
						nouns += 1

					#complements
					if ("COMP" in curr[j] or "XCOMP" in curr[j]):
						mappings[int(curr[0])] = "v" + str(verbs)
						verbs += 1

					#infinitives
					if ("INF" in curr[j]):
						inf = True
						mappings[int(curr[0])] = "inf"

					#auxilliaries
					if ("AUX" in curr[j]):
						mappings[int(curr[0])] = "aux" 
						auxs += 1

					#negatives
					if ("NEG" in curr[j]):
						curr[0] = "neg"

					#predicates
					if ("PRED" in curr[j]):
						mappings[int(curr[0])] = "pred" + str(preds)
						preds += 1
				
			for i in range(len(construction)):
				curr = construction[i].split("|")			
				#replace
				for j in range(len(curr)):
					if (curr[j].isdigit()):
						try:
							curr[j] = mappings[int(curr[j])]
						except:
							pass
				
				#deal with infinitives
				if ("INF" in curr):
					#print(curr)
					next = construction[i+1].split("|")
					if (next[1] == "x"):
						curr[1] = next[0]

				curr = "|".join(curr)
				construction[i] = curr

			construction = " ".join(construction)
			return construction



'''
CHILDES Utterance

	Contains data on a given utterance from a CHILDES format
	file.
	The constructor takes as input an extracted utterance with the 
	form:
		*(SPEAKER):	Actual transcription of the utternace
		%mor: Not important 
		%gra:	Grammatical Construction for the transcription (should 
			be a list of grammatical relations of the form 
			"node_num|taget_node|GR")
	Inherits from Utterance class
'''
class ChildesUtterance(Utterance):
	def __init__(self, text):
		#split up text
		self.speaker, self.text, self.construction = extract_from_childes(text)

	def get_speaker(self):
		return self.speaker

	def get_text(self):
		return self.text

	def get_raw_construction(self):
		return self.construction


######################################################################
#
#
#					DATA STORAGE CLASSES AND FUNCTIONS
#
######################################################################



'''
Speech data

	contains a list of childes files as well as all constructions seen
	and list of constructions in the order they are seen
	Has methods to calculate the likelihood of a construction overall
	or within a window 
'''
class SpeechData:
	def __init__(self):
		self.files = []
		self.constructions_list = []
		self.child_constructions_list = []
		self.utterances_in_order = []

	#add file and update constructions_list
	def add_file(self, filename):
		curr_file = ChildesFile(filename)
		self.files.append(curr_file)
		#add well-formed constructions from file
		for utterance in curr_file.get_utterances():
			construction = utterance.get_verb_construction()
			if (well_formed(construction)):
				#add to list of all construction
				if (construction not in self.constructions_list):
					self.constructions_list.append(construction)
				#add to list of child construction
				if (utterance.get_speaker() == "CHI"):
					if (construction not in self.child_constructions_list):
						self.child_constructions_list.append(construction)
				self.utterances_in_order.append(utterance)


	#will sort the dir before adding
	def add_from_dir(self, dirname):
		files = os.listdir(dirname)
		files.sort()
		for filename in files:
			#ignore files that are not .cha files
			if (".cha" in filename):
				print("adding from %s" % filename)
				self.add_file(str(dirname + "/" + filename))

	#get the likelihood within the window [start, end]
	#inputs: 	start and end are both ints in the range [0, 100] that represent
	#			the percentage of the constructions to consider.
	#			For example, [0, 100] is all of the data and [10, 15] breaks the data
	#			into 20 even pieces and looks only at the 3rd
	#outpus:	returns a dict of all the constructions with the likelihoods 
	#			in the given range. Applies add-1 smoothing to the likelihoods
	def get_construction_likelihoods(self, start=0, end=100):
		utterances_in_order = self.get_child_produced_in_order()
		construction_counts = {}
		total = 0.0
		#add 1 to every construction count
		for construction in self.child_constructions_list:
			construction_counts[construction] = 1
			total += 1

		start_idx = int(len(utterances_in_order)* start/100)
		end_idx = int(len(utterances_in_order) * end/100)

		for utterance in utterances_in_order[start_idx:end_idx]:
			verb_construction = utterance.get_verb_construction()
			if (verb_construction in self.child_constructions_list):
				construction_counts[verb_construction] += 1
				total += 1

		construction_likelihoods = {}
		for construction in self.child_constructions_list:
			construction_likelihoods[construction] = construction_counts[construction]/total

		return construction_likelihoods

	def get_whole_construction_list(self):
		return self.constructions_list

	def get_child_produced_list(self):
		return self.child_constructions_list

	def get_utterances_in_order(self):
		return self.utterances_in_order

	#filters list to only include constructions that child produces at some point
	def get_child_produced_in_order(self):
		child_produced = []
		for utterance in self.utterances_in_order:
			if (utterance.get_verb_construction() in self.child_constructions_list):
				child_produced.append(utterance)
		return child_produced

	#resets speech data. Used to save memory
	def clear(self):
		self.files = []
		self.constructions_list = []
		self.child_constructions_list = []
		self.utterances_in_order = []

'''
Childes file

	Contains information from a CHILDES-formatted file. 
	Keeps track of the name of the file, and keeps a list of utterances
'''
class ChildesFile:
	def __init__(self, filename):
		self.filename = filename
		self.utterance_list = extract_childes_utterances(filename)

	def get_utterances(self):
		return self.utterance_list

	def get_filename(self):
		return self.filename



