#!/usr/bin/python
import types
import glob
import os
import time
import string
#from enum import Enum

punctuation = "`~!@#$%^&*()_+-={}|[]\\:\";'<>?,./"
numeric =  "0123456789"

def hasPunctuation (stringIn) :
	global punctuation
	return len (set (stringIn).intersection (punctuation)) > 0

def hasNumeric (stringIn) :
	global numeric
	return len (set (stringIn).intersection (numeric)) > 0

def hasParens (stringIn) :
	return ('(' in stringIn or
			')' in stringIn)
			
def isAllUppercase (stringIn) :
	return stringIn.isupper ()

def isMixedCase (stringIn) :
	return not stringIn.islower () and not stringIn.isupper()

def isAllLowercase (stringIn) :
	return stringIn.islower ()

def isWhitespace (stringIn) :
	return stringIn.isspace ()

def isNumeric (stringIn) :
	return stringIn.isdigit()

def firstCharIsPound (stringIn) :
	return (len (stringIn) > 0 and
			stringIn[0] == '#')

def lastCharIsPeriod (stringIn) :
	return (len (stringIn) > 0 and
			stringIn[-1] == '.')

#recursively break up the file into a hierarchical structure

class TermColor:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

#SceneHeadingType = Enum ('traditional', 'tagged')
class SceneHeadingType :
	traditional = 0
	tagged = 1

class CustomSpecs :
	def __init__ (  self,
					sceneHeadingType=0,
					characterNameIndent=0,
					pageNumberIndent=0,
					firstDialogFragIndent=0,
					firstSceneHeadingFragIndent=0) :
		
		self.sceneHeadingType            = sceneHeadingType
		self.characterNameIndent         = characterNameIndent
		self.pageNumberIndent            = pageNumberIndent
		self.firstDialogFragIndent       = firstDialogFragIndent
		self.firstSceneHeadingFragIndent = firstSceneHeadingFragIndent 

Cars2Specs = CustomSpecs (	sceneHeadingType = SceneHeadingType.traditional,
							characterNameIndent = 25,
							pageNumberIndent = 10,
							firstDialogFragIndent = 10,
							firstSceneHeadingFragIndent = 9)

WallESpecs = CustomSpecs (	sceneHeadingType = SceneHeadingType.traditional,
							characterNameIndent = 27,
							pageNumberIndent = 64,
							firstDialogFragIndent = 20,
							firstSceneHeadingFragIndent = 8)

ShrekSpecs = CustomSpecs (	sceneHeadingType = SceneHeadingType.tagged,
							characterNameIndent = 27,
							pageNumberIndent = 64,
							firstDialogFragIndent = 20,
							firstSceneHeadingFragIndent = 8)


class LevelType :
	file = 0
	fileLines = 1
	spaceDelimitedWords = 2

class Character :
	def __init__(self, nameIn) :
		self.name = nameIn
		self.frequency = 0.0
		self.interactedWith = {} # form: {'charName': numInteractions}
	
characterList = {}

def fragLeafNodeIsAllUppercase (this) :
	return isAllUppercase (this.get ())

def fragLeafNodeIsMixedCase (this) :
	return isMixedCase (this.get ())

def fragLeafNodeIsGreaterThanOneChar (this) :
	return len (this.get ()) > 1

def fragLeafNodeIsWhitespace (this) :
	return isWhitespace (this.get ())

def fragLeafNodeIsDash (this) :
	return '-' in this.get ()

def fragLeafNodeIsOfLength (this, length) :
	#print "length = " + str (len (this.get ()))
	return len (this.get ()) == length

def fragLeafNodeLengthGreaterThan (this, length) :
	return len (this.get ()) > length

def fragLeafNodeHasParens (this) :
	return hasParens (this.get ())

def fragLeafNodeHasNumeric (this) :
	return hasNumeric (this.get ())

def fragLeafNodeHasColon (this) :
	return ':' in this.get ()

def fragLeafNodeIsLast (this) :
	return this.parentLevelIndex == len (this.parent.fragmentList) - 1

def fragLeafNodeIsARankNumber (this) :
	stringIn = this.get ()
	if not firstCharIsPound (stringIn) :
		return False

	return (len (stringIn) > 1 and
			isNumeric (stringIn[1:])) 

def fragParentHasColon (this) :
	
	if (this.parent is not None and
		this.parent.fragmentList is not None) :

		for parentNode in this.parent.fragmentList :
			if ':' in parentNode.get () :
				return True

	return False

def fragParentHasDash (this) :
	
	if (this.parent is not None and
		this.parent.fragmentList is not None) :

		for parentNode in this.parent.fragmentList :
			if '-' in parentNode.get () :
				return True

	return False

def fragParentHasParens (this) :
	
	if (this.parent is not None and
		this.parent.fragmentList is not None) :

		for parentNode in this.parent.fragmentList :
			if ('(' in parentNode.get () or
				')' in parentNode.get ()) :
				return True

	return False

def fragParentHasIDTest (this, testName) :
	
	if (this.parent is not None and
		this.parent.fragmentList is not None) :

		for parentNode in this.parent.fragmentList :
			if (testName in parentNode.IDTests and
				parentNode.IDTests[testName] == True) :
				return True

	return False

def fragBetweenIDTest (this, testName) :

	if (this.parent is not None and
		this.parent.fragmentList is not None) :
		
		
		foundIDBefore = (this.parentLevelIndex > 0 and
						 this.parent.fragmentList[this.parentLevelIndex - 1].IDTests[testName])
		
		foundIDAfter = (this.parentLevelIndex < len (this.parent.fragmentList) - 1 and
						this.parent.fragmentList[this.parentLevelIndex + 1].IDTests[testName])
		
		return (foundIDBefore and
				foundIDAfter)

	return False

def fragIsOnEdgeOfGrandParent (this) : #not counting whitespace
	return (this.parent.parentLevelIndex < 3 or
			this.parent.parentLevelIndex > len (this.parent.parent.fragmentList) - 4)

def fragLeafNodeIsAPageNumber (this) :
	stringIn = this.get ()
	if not lastCharIsPeriod (stringIn) :
		return False

	return (len (stringIn) > 1 and
			isNumeric (stringIn[:-1])) 

def parentLineContainsSceneHeadingFrag (this) :

	return (fragParentHasIDTest (this, 'firstSceneHeadingFrag'))


def fragParentFollowedByEmptyLine (this) : # expects a line
	if this.parent.parentLevelIndex < len (this.parent.parent.fragmentList) - 1:
		next = this.parent.parent.fragmentList[this.parent.parentLevelIndex + 1]
	
		return (len (next.fragmentList) == 1 and
				fragLeafNodeIsWhitespace (next.fragmentList[0]))

	else :
		return False

def fragParentFollowedBy2EmptyLines (this) :
	thisParent = this.parent
	if thisParent.parentLevelIndex > len (thisParent.parent.fragmentList) - 2 :
		return False

	nextLine = thisParent.parent.fragmentList[thisParent.parentLevelIndex + 1]
	lineAfterNextLine = thisParent.parent.fragmentList[thisParent.parentLevelIndex + 2]
	
	return (fragParentIsEmptyLine (nextLine) and
			fragParentIsEmptyLine (lineAfterNextLine))

def fragLeafNodeIsAcronym (this) :
	return 'P.S.' in this.get ()

def fragLeafNodeIsAOrI (this) :
	stringTest = this.get ()
	return (stringTest == 'A' or
			stringTest == 'I' or
			(len (stringTest) == 2 and
			 stringTest[0] == 'A' and 
			 hasPunctuation (stringTest[1])) or
			(len (stringTest) == 2 and
			 stringTest[0] == 'I' and 
			 hasPunctuation (stringTest[1])))

def fragLeafNodeIsKnownPlace (this) :
	stringTest = this.get ()
	return (stringTest == 'INT.' or
			stringTest == 'EXT.')

def fragLeafNodeHasIDTest (this, testName) :
	
	 return (testName in this.IDTests and
			 this.IDTests[testName] == True)

def fragLeafNodeIsCharFirstName (this) :
	# listed first name separated by & or 'and' or comma
	
	assert isinstance (this, Fragment), "\nfragLeafNodeIsCharFirstName () : this should be a Fragment."

	prev = this.parent.fragmentList[this.parentLevelIndex - 1]

	#what order is the fastest?
	return (fragLeafNodeIsAllUppercase (this) and
			fragLeafNodeIsWhitespace (prev) and 
			fragLeafNodeLengthGreaterThan (prev, WallESpecs.characterNameIndent) and
			not fragLeafNodeHasParens (this) and
			not fragParentHasColon (this) and
			#not fragParentHasDash (this) and
			not fragIsOnEdgeOfGrandParent(this) and
			fragLeafNodeIsGreaterThanOneChar (this))

def fragLeafNodeIsCharFirstExtension (this) :

	assert isinstance (this, Fragment), "\nfragLeafNodeIsCharFirstExtension () : this should be a Fragment."

	prev = this.parent.fragmentList[this.parentLevelIndex - 1]

	#what order is the fastest?
	return (fragLeafNodeIsAllUppercase (this) and
			fragLeafNodeIsWhitespace (prev) and 
			fragLeafNodeLengthGreaterThan (prev, WallESpecs.characterNameIndent) and
			fragLeafNodeHasParens (this) and
			not fragIsOnEdgeOfGrandParent(this) and
			fragLeafNodeIsGreaterThanOneChar (this))

def fragLeafNodeIsCharFollowingExtension (this) :

	assert isinstance (this, Fragment), "\nfragLeafNodeIsCharFollowingExtension () : this should be a Fragment."

	prev = this.parent.fragmentList[this.parentLevelIndex - 1]

	#what order is the fastest?
	return ((fragLeafNodeIsAllUppercase (this) and
			fragParentHasIDTest (this, 'characterFirstExtension')) or
			(fragLeafNodeHasParens (this) and
			("CONT'D" in this.get () or
			"O.S." in this.get () or
			"V.O." in this.get ())))

def fragLeafNodeIsDialogFirst (this) :

	assert isinstance (this, Fragment), "\nfragLeafNodeIsDialogFirst () : this should be a Fragment."

	prev = this.parent.fragmentList[this.parentLevelIndex - 1]

	#what order is the fastest?
	return ((not fragLeafNodeIsAllUppercase (this) or 
				 fragLeafNodeIsAOrI (this) or
				 fragLeafNodeHasNumeric (this) or
				 fragLeafNodeIsAcronym (this)) and
			fragLeafNodeIsWhitespace (prev) and 
			fragLeafNodeLengthGreaterThan (prev, WallESpecs.firstDialogFragIndent) and
			not fragParentHasParens (this) and
			not fragLeafNodeHasIDTest (this, 'pageNumber'))

def fragLeafNodeIsDialogFollowing (this) :
	# includes N names following first frag
	assert isinstance (this, Fragment), "\nfragLeafNodeIsDialogFollowing () : this should be a Fragment."

	return (not fragLeafNodeHasParens (this) and
			not fragLeafNodeHasIDTest (this, 'firstDialogFrag') and
			fragParentHasIDTest (this, 'firstDialogFrag'))

def fragLeafNodeIsFirstSceneHeadingFrag (this) :

	assert isinstance (this, Fragment), "\nfragLeafNodeIsFirstSceneHeadingFrag () : this should be a Fragment."

	prev = this.parent.fragmentList[this.parentLevelIndex - 1]

	#what order is the fastest?
	return (fragLeafNodeIsAllUppercase (this) and 
			not fragLeafNodeIsAOrI (this) and
			not fragLeafNodeHasNumeric (this) and
			fragLeafNodeIsKnownPlace (this) and
			fragLeafNodeIsWhitespace (prev) and 
			fragLeafNodeLengthGreaterThan (prev, WallESpecs.firstSceneHeadingFragIndent) and
			fragParentFollowedByEmptyLine (this))

def fragLeafNodeIsSceneHeadingDashFrag (this) :

	assert isinstance (this, Fragment), "\nfragLeafNodeIsFirstSceneHeadingFrag () : this should be a Fragment."

	return (parentLineContainsSceneHeadingFrag (this) and
			fragLeafNodeIsDash (this))

#	return (parentLineContainsSceneHeadingFrag (this))

def fragLeafNodeIsCharFollowingName (this) :
	# listed first name separated by & or 'and' or comma
	
	# includes N names following first name
	assert isinstance (this, Fragment), "\nfragLeafNodeIsCharFollowingName () : this should be a Fragment."

	#what order is the fastest?
	return (fragLeafNodeIsAllUppercase (this) and
			fragLeafNodeIsGreaterThanOneChar (this) and
			not fragParentHasColon (this) and
			not fragParentHasDash (this) and
			not fragLeafNodeHasParens (this) and
			not fragLeafNodeHasIDTest (this, 'characterFirstName') and
			fragParentHasIDTest (this, 'characterFirstName'))

def fragLeafNodeIsCharGenericNumber (this) : # security guard #2 type characters

	assert isinstance (this, Fragment), "\nfragLeafNodeIsCharGenericNumber () : this should be a Fragment."

	#what order is the fastest?
	return (fragLeafNodeIsARankNumber (this) and
			not fragLeafNodeHasParens (this) and
			not fragParentHasColon (this) and
			not fragParentHasDash (this) and
			fragLeafNodeIsLast (this) and
			fragLeafNodeIsGreaterThanOneChar (this))

def fragLeafNodeIsPageNumber (this) :

	assert isinstance (this, Fragment), "\nfragLeafNodeIsPageNumber () : this should be a Fragment."

	prev = this.parent.fragmentList[this.parentLevelIndex - 1]

	#what order is the fastest?
	return (fragLeafNodeIsAPageNumber (this) and
			fragLeafNodeLengthGreaterThan (prev, WallESpecs.pageNumberIndent) and
			fragParentFollowedByEmptyLine(this) and
			fragLeafNodeIsLast (this) and
			fragLeafNodeIsGreaterThanOneChar (this))

def fragParentIsSceneHeading (this) :
	pass

def fragParentIsContinuingDialog (this) :
	pass

def fragParentIsDualDialog (this) :
	pass

def fragParentIsEmphasizedDialog (this) :
	pass

def fragLeafNodeIsExtension (this) : # in parens character extension
	pass

class Fragment :

	identifyTargets = [ 
							{'name': 'characterFirstName',
							 'test' : fragLeafNodeIsCharFirstName,
							 'termColor': TermColor.OKGREEN
							},
							{'name': 'characterFirstExtension',
							 'test' : fragLeafNodeIsCharFirstExtension,
							 'termColor': TermColor.OKGREEN
							},
							{'name': 'characterFollowingExtension',
							 'test' : fragLeafNodeIsCharFollowingExtension,
							 'termColor': TermColor.OKGREEN
							},
							{'name': 'characterFollowingName',
							 'test' : fragLeafNodeIsCharFollowingName,
							 'termColor': TermColor.OKGREEN
							},
							{'name': 'characterGenericNumber',
							 'test' : fragLeafNodeIsCharGenericNumber,
							 'termColor': TermColor.OKGREEN
							},
							{'name': 'pageNumber',
							 'test' : fragLeafNodeIsPageNumber,
							 'termColor': TermColor.OKGREEN
							},
							{'name': 'firstDialogFrag',
							 'test' : fragLeafNodeIsDialogFirst,
							 'termColor': TermColor.OKGREEN
							},
							{'name': 'followingDialogFrag',
							 'test' : fragLeafNodeIsDialogFollowing,
							 'termColor': TermColor.OKGREEN
							},
							{'name': 'firstSceneHeadingFrag',
							 'test' : fragLeafNodeIsFirstSceneHeadingFrag,
							 'termColor': TermColor.FAIL
							},
							{'name': 'sceneHeadingDashFrag',
							 'test' : fragLeafNodeIsSceneHeadingDashFrag,
							 'termColor': TermColor.OKBLUE
							}
					  ]

	def set (self, content) :
		if type (content) == types.StringType :
			if len (content) == 0 :
				content = ' '
			
			self.stringFragment = content
			self.fragmentList = None
			self.isAllUppercase = isAllUppercase (content) 

		elif type (content) == types.ListType :
			self.fragmentList = content
			self.stringFragment = None

		else :
			raise Exception, "\nFragment.set (): expected either a fragment list or a string."

	def isALeafNode (self) :
		if self.stringFragment is not None :
			assert self.fragmentList is None, "\nFragment.isALeafNode (): if stringFragment is not None then fragmentList should be None." 
			return True
		
		elif self.fragmentList is not None :
			assert self.stringFragment is None, "\nFragment.isALeafNode (): if fragmentList is not None then stringFragment should be None." 
			return False

		assert self.stringFragment is None, "\nFragment.isALeafNode (): if fragmentList is not None then stringFragment should be None." 

	def get (self) :
		if self.isALeafNode() :
			return self.stringFragment
		
		else :
			return self.fragmentList
 
	def __init__ (self, contentIn=None,
						listIn=None,
						levelIn=None,
						parentIn=None,
						parentLevelIndexIn=None) :

		assert type (levelIn) == types.IntType, ("\nFragment.__init__ (): levelIn expected an Int.")

		self.level = levelIn
		
		assert type (parentLevelIndexIn) == types.IntType, ("\nFragment.__init__ (): parentLevelIndexIn expected an Int.")

		self.fragmentList = None
		self.stringFragment = None

		self.parentLevelIndex = parentLevelIndexIn

		self.parent = parentIn

		self.isAllUppercase = None
		
		self.IDTests = {}
		
		if (self.level == LevelType.file) :
			
			assert type (contentIn) == types.StringType, ("\nFragment.__init__ (): level " +
														str (self.level) +
														" expected a string.")
			assert listIn is None, ("\nFragment.__init__ (): level " +
									str (self.level) +
									" listIn should be a None.")

			lineTokens = contentIn.split ('\n')
			fragmentList = []
			for index,word in enumerate (lineTokens) : 
				fragmentList.append (Fragment (	contentIn=word,
												levelIn=LevelType.fileLines,
												parentIn=self,
												parentLevelIndexIn=index))
			
			self.set (fragmentList)

		elif (self.level == LevelType.fileLines) :
			
			assert type (contentIn) == types.StringType, ("\nFragment.__init__ (): level " +
														str (self.level) +
														" expected a string.")
			assert listIn is None, ("\nFragment.__init__ (): level " +
									str (self.level) +
									" listIn should be a None.")

			spaceTokens = contentIn.split (' ')

			fragmentList = []
			for index,word in enumerate (spaceTokens) : 
				fragmentList.append (Fragment (	contentIn=word,
												levelIn=LevelType.spaceDelimitedWords,
												parentIn=self,
												parentLevelIndexIn=index))

			self.set (fragmentList)
			
		elif (self.level == LevelType.spaceDelimitedWords) :
			
			assert type (contentIn) == types.StringType, ("\nFragment.__init__ (): level " +
														 str (self.level) +
														 " expected a string.")
			assert listIn is None, ("\nFragment.__init__ (): level " +
									str (self.level) +
									" listIn should be a None.")

			
			self.set (contentIn)

		
		else :
			raise "no level here"

	def indentationHistogram (self) :
		histogram = {}
		# lines in file
		for lineFragment in self.fragmentList :
			if len (lineFragment.fragmentList) > 0 :
				print lineFragment.get ()
				firstFrag = lineFragment.fragmentList[0]
				print len (firstFrag.get ())
				time.sleep (0.2)
				if isWhitespace (firstFrag.get ()) :
					#print len (firstFrag.get ())
					if len (firstFrag.get ()) in histogram :
						histogram[len (firstFrag.get ())] += 1
						
					else :
						histogram[len (firstFrag.get ())] = 1

		print histogram
		exit (0)

	def collapseLeadingWhitespaceSequence (self) :
		#collapse many leading whitespace fragments into one

		assert self.level == LevelType.fileLines, "\nFragment.collapseLeadingWhitespaceSequence (): should only be called on LevelType.fileLines fragments"

		if (not self.isALeafNode () and
			len (self.fragmentList) > 1) :
			
			firstFragment = self.fragmentList[0]

			assert firstFragment.isALeafNode (), "\nFragment.collapseLeadingWhitespaceSequence (): first fragment should be a leaf node"

			if isWhitespace (firstFragment.get ()) :
				newWhitespaceFragmentLength = 0

				for index,word in enumerate (self.fragmentList) :
					if not isWhitespace (word.get ()) :
						break
					
					newWhitespaceFragmentLength += 1

				newWhitespaceFragment = Fragment (	contentIn=' ' * (newWhitespaceFragmentLength - 1),
													levelIn=LevelType.spaceDelimitedWords,
													parentIn=firstFragment.parent,
													parentLevelIndexIn=firstFragment.parentLevelIndex)

				if newWhitespaceFragmentLength < len (self.fragmentList) :
					newFragmentList = [newWhitespaceFragment]
					newFragmentList.extend (self.fragmentList[newWhitespaceFragmentLength:])
					for index, fragment in enumerate (newFragmentList) :
						fragment.parentLevelIndex = index

					self.fragmentList = newFragmentList

				else :
					self.fragmentList = [Fragment (	contentIn='',
													levelIn=LevelType.spaceDelimitedWords,
													parentIn=firstFragment.parent,
													parentLevelIndexIn=firstFragment.parentLevelIndex)]

	def process1 (self) :
		
		# descend down through the levels until we are at the target level then run the process, then return
		targetLevel = LevelType.fileLines
		if not self.isALeafNode () :
			for fragment in self.fragmentList :
				if fragment.level > targetLevel :
					fragment.process1 ()
				
				elif fragment.level == targetLevel :
					fragment.collapseLeadingWhitespaceSequence ()
				
				else :
					return

	def process2 (self) :
		# build the character list
		assert self.level == LevelType.file, "process2(): level should be file"

		
		# lines in file
		for lineFragment in self.fragmentList :
			charName = ''
			for wordFragment in lineFragment.fragmentList :

				if (('characterFirstName' in wordFragment.IDTests and
					 wordFragment.IDTests['characterFirstName'] == True) or
					('characterFollowingName' in wordFragment.IDTests and
					 wordFragment.IDTests['characterFollowingName'] == True) or
					('characterGenericNumber' in wordFragment.IDTests and
					 wordFragment.IDTests['characterGenericNumber'] == True)) :

					if len (charName) > 0 :
						charName += ' '

					charName += wordFragment.get ()

			if len (charName) > 0 :
				if charName not in characterList.keys () :
					characterList[charName] = Character (charName)

				characterList[charName].frequency += 1

	def anyIDTestIsTrue (self) :
		for test in self.IDTests.keys () :
			if self.IDTests[test] == True :
				return True

		return False

	def identifyLeafNodes1 (self) :

		# descend down through the levels until we are at the target level then run the process, then return
		targetLevel = LevelType.spaceDelimitedWords
		if self.isALeafNode () :
			for target in Fragment.identifyTargets :
				if self.anyIDTestIsTrue () :
					break

				self.IDTests[target['name']] = target['test'] (self)

		else :
			for fragment in self.fragmentList :
				fragment.identifyLeafNodes1 ()

	def getIDType (self, name) :
		for index,search in enumerate (self.identifyTargets) :
			if search['name'] == name :
				return index

		return None

	def color (self) :
		if len (self.IDTests.keys ()) > 0 :
			colors = ''
			#for target in self.identifyTargets :
			for target in self.IDTests.keys () :
				if self.IDTests[ target ] == True :
					colors += self.identifyTargets[self.getIDType (target)]['termColor']

			return colors + self.get () + TermColor.ENDC

		else :
			return self.get ()

	def __repr__ (self) :
		if self.isALeafNode () :
			if self.level == LevelType.spaceDelimitedWords :
				# don't put a space after the last word in the line
				if self.parentLevelIndex < len (self.parent.fragmentList) - 1 :
					return self.color () + ' ' # alpha word

				elif (len (self.parent.fragmentList) == 1 and 
					  len (self.stringFragment) == 1 and
					  self.stringFragment == ' ') :
					return '' # empty line

				else :
					return self.color () # end of line

		else :
			stringOut = ""
			for fragment in self.fragmentList :
				stringOut += fragment.__repr__ ()

			if self.level == LevelType.fileLines :
				# don't put a space after the last word in the line
				if self.parentLevelIndex < len (self.parent.fragmentList) - 1 : 
					return stringOut + '\n'
				
				else :
					return stringOut # end of file

			else :
				return stringOut #end of file

		raise Exception, "\nFragment.__repr__ (): unable to create string from fragment."

#overlay transform to get two different sets to a comparable state, so that parts of the two can be swapped and
# still end up with a valid result

def roundTripTest () :
	if os.environ["HOST"] == 'Rhetts-MacBook-Pro.local' :
		filePath = "/Users/rhett/workspace/script1"
		
	else :
		filePath = "/Users/rhettcollier/workspace/script1"
		
	print filePath + "/training/*.txt"
	filenames = glob.glob (filePath + "/training/*.txt")
	print filenames

	for index,filename in enumerate (filenames) :
		if index == 1 :
			fileHandle = open ( filename, 'r')
			fileString = fileHandle.read ()
			fileHandle.close ()
		
			scriptOut = Fragment (	contentIn=fileString, 
									parentLevelIndexIn=0, 
									levelIn=LevelType.file)
	
			scriptOut.process1 ()
			#scriptOut.indentationHistogram ()
			scriptOut.identifyLeafNodes1 ()
			scriptOut.process2 ()
			
			print scriptOut.__repr__ ()
	
			charsSorted = [(char.frequency,char) for key,char in characterList.iteritems ()]
			charsSorted.sort (reverse=True)
	
			for char in charsSorted :
				print '"' + char[1].name + '"    '+ str ( int (char[1].frequency))
	
			#exit(0)
			print "original: " + str (len (fileString)) + "  __repr__: " + str (len (scriptOut.__repr__ ()))
			
			scriptFile = open (filePath + "/roundTrip" + os.path.basename (filename), 'w')
			scriptFile.write (scriptOut.__repr__ ())
			scriptFile.close ()
			break
	
roundTripTest()


