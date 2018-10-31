import numpy as np

'''
Get Length complexity

	inputs: construction is a string of GR's of the form 
			"node_num|taget_node|GR"
			remove_subjects is a bool. If True, remove any 
			word with the GR "SUBJ"

	outputs: returns the length of construction (after removing
				subjects if remove_subjects is True)
'''
def get_length_complexity(construction, remove_subjects):
	words = construction.split()
	
	#prune subjects 
	if (remove_subjects):
		for i in range(3):
			for word in words:
				if ("SUBJ" in word): 
					words.remove(word)

	return len(words)


'''
levenshtein

	inputs: key1 is the construction being compared to key2.
			both should be strings of GR's of the form 
			"node_num|taget_node|GR"
	outputs: returns the levenshtein edit distance between 
			key1 and key2.
	description: calculates levenshtein edit distance using 
			dynamic programming.
			Algorithm implemented as shown here: 
			http://stackabuse.com/levenshtein-distance-and-text-similarity-in-python/
'''
def levenshtein(key1, key2):
	key1 = key1.split()
	key2 = key2.split()

	size_x = len(key1) + 1
	size_y = len(key2) + 1
	matrix = np.zeros((size_x, size_y))
	for x in xrange(size_x):
		matrix[x, 0] = x
	for y in xrange(size_y):
		matrix[0, y] = y

	for x in xrange(1, size_x):
		for y in xrange(1, size_y):
			if key1[x-1] == key2[y-1]:
				matrix[x, y] = min(matrix[x-1, y] + 1, matrix[x-1, y-1], matrix[x, y-1] + 1)
			else:
				matrix[x,y] = min(matrix[x-1, y] + 1, matrix[x-1, y-1] + 1, matrix[x, y-1] + 1)

	return (matrix[size_x-1, size_y-1])

'''
Modified levenshtein

	inputs: key1 is the construction being compared to key2.
			both should be strings of GR's of the form 
			"node_num|taget_node|GR"
	outputs: returns the modified levenshtein edit distance between 
			key1 and key2 
	description: Same as levenshtein, but with the modification that 
			if the GR is not changed in a swap, only 0.5 is counted towards
			the total.
			For example "x|0|ROOT n1|x|SUBJ" and "x|0|ROOT n1|v1|SUBJ v1|x|COMP"
			would only have a modified distance of 1.5 instead of 2 under the
			regular levenshtein
'''
def modified_levenshtein(key1, key2):
	key1 = key1.split()
	key2 = key2.split()

	key2_grs = []
	for word in key2:
		key2_grs.append(word.split("|")[2])

	size_x = len(key1) + 1
	size_y = len(key2) + 1
	matrix = np.zeros((size_x, size_y))
	for x in xrange(size_x):
		matrix[x, 0] = x
	for y in xrange(size_y):
		matrix[0, y] = y

	for x in xrange(1, size_x):
		for y in xrange(1, size_y):
			if key1[x-1] == key2[y-1]:
				matrix[x, y] = min(matrix[x-1, y] + 1, matrix[x-1, y-1], matrix[x, y-1] + 1)
			#if the modification doesn't change the GR, only add .5
			elif (key1[x-1].split("|")[2] == key2[y-1].split("|")[2]):
				matrix[x, y] = min(matrix[x-1,y] + 1, matrix[x-1, y-1] + .5, matrix[x, y-1] + 1)					
			else:
				matrix[x,y] = min(matrix[x-1, y] + 1, matrix[x-1, y-1] + 1, matrix[x, y-1] + 1)

	return (matrix[size_x-1, size_y-1])




'''
Overall levenshtein

	inputs:	const_dict is a list of known constructions.
			construction is the construction you want to find the min 
			levenshtein distance for. Should be a string of GR's of the form 
			"node_num|taget_node|GR"
	outputs: finds the levenshtein distance between construction and
			every construction in const_list. Returns the min 
			levenshtein distance.

'''
def overall_levenshtein(construction, const_list):
	#if const_list is empty, complexity = num of GRs
	if (const_list == []):
		return float(len(construction.split()))
	#otherwise, complexity = lowest levenshtein score 
	else:
		#100 is used as an arbitrarily large number
		result = 100
		for key in const_list:
			result = min(result, levenshtein(construction, key))
		return result


'''
Overall modified levenshtein

	same as overall_levenshtein, but modified levenshtein distance
	used instead of regular levenshtein distance
'''
def overall_modified_levenshtein(construction, const_list):
	#if const_list is empty, complexity = num of GRs
	if (const_list == []):
		return float(len(construction.split()))
	#otherwise, complexity = lowest levenshtein score 
	else:
		#100 is used as an arbitrarily large number
		result = 100
		for key in const_list:
			result = min(result, modified_levenshtein(construction, key))
		return result