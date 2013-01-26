
import sys, os

from grammar_parser import *

comment_prefix = "annotation:"

args = sys.argv[:] # copy of arguments
args.pop(0) # remove first entry

inputfile = outpufile = None

while len(args) > 0:
  arg = args.pop(0)
  if arg == '-i': inputfile = os.path.abspath(args.pop(0))
  elif arg == '-o': outputfile = os.path.abspath(args.pop(0))
  else:
    print "Unknown argument."
    raise SystemExit

if not inputfile or not outputfile:
  print "Give inputfile with -i PATH and outpufile with -o PATH."
  raise SystemExit

print "Parsing input file \""+inputfile+"\" ..."
grammar = grammar_parse(inputfile)
print str(len(grammar['tokens']))+" tokens, "+str(len(grammar['types']))+" types."

print "Generating annotations ..."

type_annos = []
for t in grammar['types']:
  used_count = 0 # Count occurrences on right side of rules
  used_in = []
  duplicates = 0 # Count number of blocks with this type on left side
  
  for rule in grammar['rules']:
    # duplicates
    if rule['left'] == t:
      duplicates += 1
    
    # used in
    used = False
    for production in rule['right']:
      for symbol in production:
        if symbol == t:
          used_count += 1
          used = True
    if used: used_in.append(rule['left'])
  type_annos.append({'name': t, 'duplicates': duplicates, 'used_count': used_count, 'used_in': used_in})

print type_annos

print "Writing annotations to \""+outputfile+"\" ..."

inf = open(inputfile, "r")
outf = open(outputfile, "w")

annotation_regex = re.compile(r'^\/\/'+comment_prefix+'')
rulegroupstart_regex = re.compile(r'^\s*(\w+)\s*\:\s*$', re.MULTILINE);
for line in inf:
  mo = annotation_regex.match(line)
  if mo: continue
  
  mo = rulegroupstart_regex.match(line)
  if mo:
    # print annotation
    annos = [anno for anno in type_annos if anno['name'] == mo.group(1)]
    if len(annos) != 1:
      print "Found some rule, that I must have missed a moment ago: "+mo.group(1)
    anno = annos.pop(0)
    if anno['used_count'] is 0: outf.write("//"+comment_prefix+" This type is not used anywhere")
    elif anno['used_count'] is 1: outf.write("//"+comment_prefix+" This type is used only once in")
    else: outf.write("//"+comment_prefix+" This type is used "+str(anno['used_count'])+" times in\n//"+comment_prefix)
    for u in anno['used_in']: outf.write(" "+u)
    outf.write('\n');
  outf.write(line)

inf.close()
outf.close()

print "Done."

