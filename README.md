bison-annotations
=================

Generate annotations about the usage of rules directly in the grammar file.

Execute the main script with:

```python main.py -i inputgrammar.y -o outputgrammar.y```

The output file is a perfect copy of the input file except that old annotations are deleted and new ones are generated. I have not tested, what happens, if you give the same file as input and output. You should delete the input file and rename the output file if you want. Be careful: This script may fail on weird input and the output file may be empty in that case :-)

The resulting annotations look like these:

```
//annotation: This type is used 3 times in
//annotation: enum_specifier enumerator_list
enumerator_list:
      enumerator
    | enumerator_list ',' enumerator
;
```

First it says how often it is used, then where. Because one symbol may have more than one production with more than one symbol each, the number how often something is used is normally larger than the list of symbols where it is used.

## Formatting of grammar file

The token and type declarations in the grammar have to look like these:

```
%token TYPE1 TYPE2 TYPE3
/* or */
%token <...> TYPE1 TYPE2 TYPE3

%type <...> TYPE1 TYPE2 TYPE3
```

Rules in the grammar have to look similar to this one:

```
primary_expression:
      identifier
      /* Comment */
    | INTEGER
    | CHARACTER
    | FLOATING
    | STRING
    | '(' expression ')' { ... code {more code ...} }
/* Another Comment */
;
```

* The left side of the productions `primary_expression:` must go into one single line with no other characters except whitespaces.
* You may make comments with `/* ... */` or `//`
* Lines beginning with `//annotations:` are ignored when rewriting the file thus old annotations vanish.
