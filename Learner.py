from collections import namedtuple
from abc import abstractmethod
import Helper
import random


'''
Learner

	abstract base class for all learner classes.
	Can keep track of the counts of constructions and 
	which constructions are known.
	Has methods to take in input and determine if a 
	construction is known, but all other methods
	are abstract
'''
class Learner:
	def __init__(self):
		self.seen_counts = {}
		self.known_constructions = []

	def take_input(self, construction):
		#update seen_counts
		if (construction not in self.seen_counts):
			self.seen_counts[construction] = 0
		self.seen_counts[construction] += 1

		#check if already known. If not, check if it is now learned
		if (construction not in self.known_constructions):
			if (self.learn_construction(construction)):
				self.known_constructions.append(construction)

	def predict_known(self, construction):
		if (construction in self.known_constructions):
			return True
		else:
			return False

	def reset(self):
		self.seen_counts = {}
		self.known_constructions = []

	def get_known(self):
		return self.known_constructions

	def get_seen_counts(self):
		return self.seen_counts

	@abstractmethod
	def learn_construction(self, construction):
		pass


'''
Frequentist Learner

	learn_construction checks whether the seen count for the 
	word is over the threshold value. If yes, the construciton
	is learned
'''
class FrequentistLearner(Learner):
	def __init__(self, learn_times=10):
		Learner.__init__(self)
		self.learn_times = int(learn_times)

	def learn_construction(self, construction):
		try:
			if (self.seen_counts[construction] >= self.learn_times):
				return True
			else:
				return False
		except Exception as error:
			print("Problem in learn_construction: %s" % error)

	def get_type(self):
		return "frequentist"

	def get_learn_times(self):
		return self.learn_times


'''
ComplexityBased Learner

	Learns constructions probabilistically based on their relative 
	complexity to the known constructions.
	Probability_dict maps complexities onto probabilities. If a 
	complexity is not in probability dict: 
		-if it is between two complexities that are in the dict, 
		 	average them
	 	-if not, assume 0
	learn_construction checks the complexity of the given 
	construction and uses the probability_dict to determine if it 
	is learned
'''
class ComplexityBasedLearner(Learner):
	def __init__(self, probability_dict={1.0: 1.0}):
		Learner.__init__(self)
		self.probability_dict = probability_dict

	def learn_construction(self, construction):
		complexity = Helper.overall_modified_levenshtein(construction, self.known_constructions)
		probability = self.get_probability(complexity)
		if (self.check_if_learned(probability)):
			return True
		else:
			return False

	
	def get_probability(self, complexity):
		#in probability dict
		if (complexity in self.probability_dict.keys()):
			return self.probability_dict[complexity]
		else:
			#check if complexity is average of two numbers in probability dict
			for prob1 in self.probability_dict.keys():
				for prob2 in self.probability_dict.keys():
					if (complexity == (prob1 + prob2)/2):
						return ((self.probability_dict[prob1] + self.probability_dict[prob2])/2)
			#if it gets here, it is not between two numbers in probability dict
			return 0

	def check_if_learned(self, probability):
		random_number = random.random()
		if (random_number < probability):
			return True
		else:
			return False

	def get_type(self):
		return "ComplexityBased"

	def get_probability_dict(self):
		return self.probability_dict




'''
Threshold Learner

	Gains knowledge of each construction based on relative complexity.
	If this knowledge value passes a threshold, the construction is learned.
	threshold is the value that must be passed.
	complexity_dict maps complexity onto knowledge. If value is not in 
	complexity_dict, check if it is the average of 2 values. Otherwise, use 0
'''
class ThresholdLearner(Learner):
	def __init__(self, threshold=10, complexity_dict={0.0: 10, 0.5:8, 1.0: 5, 1.5: 3, 2: 1}):
		Learner.__init__(self)
		self.threshold = threshold
		self.complexity_dict = complexity_dict
		#keep track of the progess toward learning each construction
		self.progress = {}

	def take_input(self, construction):
		#update seen_counts
		if (construction not in self.seen_counts.keys()):
			self.seen_counts[construction] = 0
		self.seen_counts[construction] += 1

		#update progress
		if (construction not in self.progress.keys()):
			self.progress[construction] = 0
		complexity = Helper.overall_modified_levenshtein(construction, self.known_constructions)
		self.progress[construction] += self.calculate_progress(complexity)

		#check if already known. If not, check if it is now learned
		if (construction not in self.known_constructions):
			if (self.learn_construction(construction)):
				self.known_constructions.append(construction)

	def calculate_progress(self, complexity):
		#in complexity dict
		if (complexity in self.complexity_dict.keys()):
			return self.complexity_dict[complexity]
		else:
			#check if complexity is average of two numbers in complexity dict
			for comp1 in self.complexity_dict.keys():
				for comp2 in self.complexity_dict.keys():
					if (complexity == (comp1 + comp2)/2):
						return ((self.complexity_dict[comp1] + self.complexity_dict[comp2])/2)
			#if it gets here, it is not between two numbers in complexity dict
			return 0


	def learn_construction(self, construction):
		if (self.progress[construction] >= self.threshold):
			return True
		else:
			return False

	def get_progress(self):
		return self.progress

	def get_type(self):
		return "threshold"

	def get_threshold(self):
		return self.threshold

	def get_complexity_dict(self):
		return self.complexity_dict







