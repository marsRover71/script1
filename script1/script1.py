#!/usr/bin/python
import types
import copy

print "script1"

filename = "/Users/rhett/Documents/cars2.txt"

fileHandle = open (filename, 'r')
fileLines = fileHandle.readlines ()
fileHandle.close ()

#recursively break up the file into a heirarchical structure

level_file = 0
level_fileLines = 1
level_spaceDelimitedWords = 2
	
class Fragment :
	def __init__ (self, stringIn=None,
						listIn=None,
						levelIn=None) :

		assert type (levelIn) == types.IntType, ("levelIn expected an Int.")

		if (levelIn == level_file) :
			
			assert type (stringIn) == types.StringType, ("level " +
														str (levelIn) +
														" expected a string.")
			assert type (listIn) == None, ("level " +
											str (levelIn) +
											" listIn should be a None.")
			assert listIn[-1] == '\n', ("level " +
										str (levelIn) +
										" expected a line with a newline character.")
			print "level: level_fileLines"
			spaceTokens = stringIn.split (' ')
			self.fragmentList = []#Fragment (listIn=spaceTokens, levelIn=level_spaceDelimitedWords)
			for word in spaceTokens : 
				self.fragmentList.append (Fragment (stringIn=word, levelIn=level_spaceDelimitedWords))

		elif (levelIn == level_fileLines) :
			
			assert type (stringIn) == types.StringType, ("level " +
														str (levelIn) +
														" expected a string.")
			assert type (listIn) == None, ("level " +
											str (levelIn) +
											" listIn should be a None.")
			assert listIn[-1] == '\n', ("level " +
										str (levelIn) +
										" expected a line with a newline character.")
			print "level: level_fileLines"
			spaceTokens = stringIn.split (' ')
			self.fragmentList = []#Fragment (listIn=spaceTokens, levelIn=level_spaceDelimitedWords)
			for word in spaceTokens : 
				self.fragmentList.append (Fragment (stringIn=word, levelIn=level_spaceDelimitedWords))

		elif (levelIn == level_spaceDelimitedWords) :
			
			print "string"
			assert type (stringIn) == types.StringType, ("level " +
													 str (levelIn) +
													 " expected a string.")
			assert type (listIn) == None, ("level " +
											str (levelIn) +
											" listIn should be a None.")

			
			self.fragmentList = stringIn

		elif (type (listIn) == types.ListType and
			len (listIn) > 0 and
			type (listIn[0]) == types.StringType) :

			newList = copy.deepcopy (listIn)
			for index,fragment in enumerate (listIn) :
				newList[index] = Fragment (fragment)

			self.fragmentList = newList
			print "fragment"
		
	
	def __repr__ (self) :
		if type (self.fragmentList) == types.StringType :
			return self.fragmentList

		else :
			stringOut = ""
			for fragment in self.fragmentList :
				stringOut += fragment.__repr__ ()
			return stringOut

script = Fragment (listIn=fileLines,levelIn=level_fileLines)
print script
#print fileLines

punctuation = "`~!@#$%^&*()_+-={}|[]\\:\";'<>?,./"

def stringHasPunctuation (stringIn) :
	global punctuation
	return len (set (stringIn).intersection (punctuation)) > 0

def tokenize (line) :
	tokens = line.strip ().rstrip ().split (' ')
#	 newTokens = []
#	 for index, token in enumerate (tokens) :
#		 if stringHasPunctuation (token) :
#			 punctuationTokenize ()
#			 
#		 else :
#			 newTokens.append (token)
	return tokens
