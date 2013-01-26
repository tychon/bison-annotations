
import sys

from grammar_parser import *

args = sys.argv[:] # copy of arguments
args.pop(0) # remove first entry

inputfile = None

while len(args) > 0:
  arg = args.pop(0)
  inputfile = arg

print "Parsing input file ..."
grammar = grammar_parse(inputfile)
grammar_deduplicate(grammar)
print str(len(grammar['tokens']))+" tokens, "+str(len(grammar['types']))+" types."

