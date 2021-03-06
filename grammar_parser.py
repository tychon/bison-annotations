
# Copyright (C) 2013 Hannes Riechert <tychon4.2@gmail.com>
# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See the LICENSE file for more details.

import re, mmap

# Returns an dictionary 'ret' with this structure:
# res['inputfile'] = inputfile
# res['declared_tokens'] = [list of all tokens declared in bison declarations (before first '%%')]
# res['implicit_tokens'] = [list of all tokens implicitly declared in rules, not in bison declarations]
# res['tokens'] = the union of declared_tokens and implicit_tokens
# res['declared_types'] = [list of all types declared in bison declarations]
# res['implicit_types'] = [list of all types implicitly declared in rules, not in bison declarations]
# res['types'] = the union of declared_types and implicit_types
# res['start_type'] = the start type declared in header (may be None, if it is not declared in bison declarations)
# res['rules'] = {'left': string giving the type, 'right': [[list of tokens for every production]]}
# 
# This function may return None if there was a failure during parsing.
def grammar_parse(inputfile):
  inputf = None
  mmappedfile = None
  try:
    inputf = open(inputfile, "r+b")
    mmappedfile = mmap.mmap(inputf.fileno(), 0)
  except IOError, message: # Fehlerbehandlung
    print "Couldn't map input file into memory:"
    print message
    return None
  
  result = {'inputfile': inputfile}
  
  ####### Read in declarations
  # read token declarations
  token_regex = re.compile(r'^\s*%token(?:\s*<.*>)?((?:\s+\w+)+)\s*$', re.MULTILINE)
  tokens = []
  for match in token_regex.finditer(mmappedfile):
    tokens.extend(match.group(1).split())
  result['declared_tokens'] = tokens
  
  # read type declarations
  type_regex = re.compile(r'^\s*%type(?:\s*<.*>)?((?:\s+\w+)+)\s*$', re.MULTILINE)
  types = []
  for match in type_regex.finditer(mmappedfile):
    types.extend(match.group(1).split())
  result['declared_types'] = types
  
  # read in start symbol
  startsym_regex = re.compile(r'^\s*%start\s+(\w+)\s*$', re.MULTILINE)
  startsymbol = None
  for match in startsym_regex.finditer(mmappedfile):
    if startsymbol:
      print "Multiple definition of startsymbol with start!"
      return None
    startsymbol = match.group(1)
  result['start_type'] = startsymbol
  
  implicit_types = []
  implicit_tokens = []
  ####### Read in beginnings of rules and the boundaries of their bodies:
  rulegroupstart_regex = re.compile(r'^\s*(\w+)\s*\:\s*$', re.MULTILINE)
  rules = [] # list of [{left:string_type, start: int_index, end: int_index}]
  for match in rulegroupstart_regex.finditer(mmappedfile):
    # add to implicit types, if not found in types:
    if not (match.group(1) in types): implicit_types.append(match.group(1))
    # save beginning and end of match
    rules.append({'left': match.group(1), 'start': match.start(), 'end': match.end()})
  
  ####### Parse bodies of rules
  for ruleindex in range(len(rules)):
    rule = rules[ruleindex]
    startindex = rule['end']
    if ruleindex < len(rules)-1: endindex = rules[ruleindex+1]['start']
    else:
      # handle last rule-group right
      mo = re.search('^%%$', mmappedfile[startindex:], re.MULTILINE);
      if not mo:
        print "No end of grammar definitions found!"
        return None
      endindex = mo.start() + startindex
    ruleright = mmappedfile[startindex:endindex] # this is the body of the rule
    
    # delete multiline comments
    comment_regex = re.compile(r'/\*|\*/')
    commentstart = -1
    while True:
      mo = re.search(comment_regex, ruleright)
      if not mo: break
      commentstart = mo.start()
      mo = re.search(comment_regex, ruleright[commentstart+2:])
      if not mo:
        print "Missing closing comment symbol in rules for '"+rule['left']+"'"
        print "Remember: only comments over one group of rule are allowed!"
        return None
      ruleright = ruleright[:commentstart] + ruleright[commentstart+2+mo.end():]
    # delete one line comments
    comment_regex = re.compile(r'(\/\/[^\n]*\n)');
    while True:
      mo = re.search(comment_regex, ruleright)
      if not mo: break
      ruleright = ruleright[:mo.start(1)] + ruleright[mo.end(1):]
    
    # delete code in curly braces
    curlybrace_regex = re.compile(r"[^'](\{)[^']|[^'](\})[^']")
    currentpos = 0
    codestart = -1 # gives the position of the first brace
    level = 0 # gives the level of nested braces
    while True: # forever
      mo = re.search(curlybrace_regex, ruleright[currentpos:])
      if not mo:
        if level > 0:
          print "Missing curly brace in rules for '"+rule['left']+"', nesting level: "+str(level)+" Code:"
          print ruleright
          return None
        break
      else:
        if mo.group(1) == '{':
          level += 1
          if codestart < 0: codestart = currentpos + mo.start(1)
          currentpos += mo.end(1)
        elif mo.group(2) == '}':
          if level is 0:
            print "Too much closing curly braces in rules for '"+rule['left']+"'"
            return None
          level -= 1
          if level is 0:
            # delete found codelet
            ruleright = ruleright[:codestart] + ruleright[currentpos+mo.end(2):]
            currentpos = codestart
            codestart = -1
          else:
            currentpos += mo.end(2)
        else:
          print "Info update from your regular expression logic: BOOOOOM!"
          return None
    
    # split into single rules
    singlerules = [[]]
    for token in ruleright.split():
      if token == ';': break;
      if token == '|': singlerules.append([])
      else:
        if (not (token in tokens)
            and not (token in implicit_tokens)):
          implicit_tokens.append(token)
        singlerules[len(singlerules)-1].append(token)
    rule['right'] = singlerules
  
  readyrules = []
  for rule in rules:
    productions = []
    readyrules.append({'left': rule['left'], 'right': rule['right']})
  result['rules'] = readyrules
  
  result['implicit_types'] = implicit_types
  types.extend(implicit_types)
  result['types'] = types
  
  index = 0
  while (index < len(implicit_tokens)):
    if implicit_tokens[index] in types: implicit_tokens.pop(index)
    else: index += 1
  
  result['implicit_tokens'] = implicit_tokens
  tokens.extend(implicit_tokens)
  result['tokens'] = tokens
  
  mmappedfile.close()
  inputf.close()
  
  return result

# This function should find productions for the same not terminal symbol and
# put them all into one rule.
def grammar_deduplicate(grammar):
  index1 = 0
  rules = grammar['rules']
  while index1 < len(rules):
    index2 = index1+1
    while index2 < len(rules):
      if rules[index2]['left'] == rules[index1]['left']:
        # found duplicate rule
        rules[index1]['right'].extend(rules[index2]['right'])
        rules.pop(index2)
      else: index2 += 1
    index1 += 1

