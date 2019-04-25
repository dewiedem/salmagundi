# Programming with PyCIFRW

PyCIFRW provides facilities for reading, manipulating and writing 
CIF and STAR files. In addition, CIF files and dictionaries may 
be validated against DDL1/2/m dictionaries. 

## Installing and Initialising PyCIFRW

(Note: these instructions refer to version 4.0 and higher. For
older versions, see the documentation provided with those versions).

As of version 4.0, it is sufficient to install the PyCIFRW “wheel” 
using `pip`, for example: 

    pip install --use-wheel PyCifRW-4.2-cp27-none-linux_i686.whl

or using the platform independent source package found on PyPI:

    pip install pycifrw

If you want to include PyCIFRW with your package, you can install the
PyCIFRW wheel into your development environment and then bundle the
contents of the `CifFile` directory found in the Python local
libraries directory (usually `site-packages`).

If PyCIFRW has installed properly, the following command should
complete without any errors:

      import CifFile

## Working with CIF files

### Reading CIF files

CIF files are represented in PyCIFRW as `CifFile` objects. These 
objects behave identically to Python dictionaries, with some 
additional methods. `CifFile` objects can be created by calling the 
`ReadCif` function on a filename or URL:

          from CifFile import ReadCif
          cf = ReadCif("mycif.cif")    
          df = ReadCif("ftp://ftp.iucr.org/pub/cifdics/cifdic.register")

Errors are raised if CIF syntax/grammar violations are 
encountered in the input file or line length limits are exceeded.

A compiled extension (`StarScan.so`) is available in binary
distributions which increases parsing speed by a factor of three or
more. To use this facility, include the keyword argument
`scantype='flex'` in `ReadCif` commands:

          cf = ReadCif("mycif.cif",scantype="flex")

Binary distributions are generally only provided for the 'manylinux'
target, but may also be generated from the source distribution for any
platform if the appropriate compilers are available on that platform.

Alternatively, you may initialise a CifFile object with the URI:

          cf = CifFile("mycif.cif",scantype="flex")

If your CIF file contains characters that are not encoded in UTF8 or
ASCII, you may pass the 'permissive' option to `ReadCif`, which will
try other encodings (currently only `latin1`).  Use of this option
is not encouraged.

#### Grammar options

There are three variations in CIF file syntax.  An early, little-used
version of the standard allowed non-quoted data strings to begin with
square bracket characters ('['). This was disallowed in version 1.1 in
order to reserve such usage for later developments.  The recently
introduced CIF2 standard adds list and table datastructures to
CIF1. Detection of the appropriate CIF grammar is automatic, but
potentially time-consuming for multiple files, so specification of the
particular version to use is possible with the grammar keyword:

         cf = ReadCif('oldcif.cif',grammar='1.0') #oldest CIF syntax      
         cf = ReadCif('normcif.cif',grammar='1.1') #widespread
         cf = ReadCif('future.cif',grammar='2.0') #latest standard
         cf = ReadCif('unknown.cif',grammar='auto') #try 2.0->1.1->1.0

Reading of STAR2 files is also possible by setting `grammar='STAR2'`.
Currently, the default is set to 'auto'.

### Creating a new CifFile

A new `CifFile` object is usually created empty:

~~~{.python}
        from CifFile import CifFile
        cf = CifFile()
~~~

You will need to create at least one `CifBlock` object to hold your 
data.  The `CifBlock` is then added to the `CifFile` using the usual
Python dictionary notation.  The dictionary 'key' becomes the 
blockname used for output.

~~~{.python}
        from CifFile import CifBlock
        myblock = CifBlock()        
        cf['a_block'] = myblock
~~~

A `CifBlock` object may be initialised with another `CifBlock`, in 
which case a copy operation is performed.

Note that most operations on data provided by PyCIFRW involve
`CifBlock` objects.

## Manipulating values in a CIF file

### Accessing data

The simplest form of access is using standard Python square 
bracket notation. Data blocks and data names within each data 
block are referenced identically to normal Python dictionaries:

~~~{.python}
      my_data = cf['a_data_block']['_a_data_name']
~~~

All values read in are stored as strings ^[
This deviates from the current CIF standard, which mandates 
interpreting unquoted strings as numbers where possible and in 
the absence of dictionary definitions to the contrary 
(International Tables, Vol. G., p24).
],  with CIF syntactical 
elements stripped, that is, no enclosing quotation marks or semicolons are 
included in the values. The value associated with a `CifFile` 
dictionary key is always a `CifBlock` object. All standard Python 
dictionary methods (e.g. `get`, `update`, `items()`, `keys()`) are available 
for both `CifFile` and `CifBlock` objects. Note also the convenience 
method `first_block()`, which will return the first datablock stored _which
is not necessarily the first datablock in the physical file_:

~~~{.python}
    my_data = cf.first_block()
~~~

If a data name occurs in a loop, a list of values is 
returned for the value of that dataname - the next section 
describes ways to access looped data.

#### Tabular (“looped”) data

For the purpose of the examples, we use the following 
example CIF file:

~~~~~~~~~~~~~~
data_testblock
loop_
  _item_5   
  _item_7   
  _item_6    
  1  a  5    
  2  b  6    
  3  c  7    
  4  d  8 
~~~~~~~~~~~~~~~

Any table can be interacted with in a column-based
or a row-based way.  A PyCIFRW `CifBlock` object provides
column-based access using normal square bracket syntax
as described above: for example `cf['testblock']['_item_6']`
will return `['5','6','7','8']`.

#### Table row access

The `CifLoopBlock` object represents a loop structure in the CIF file
and facilitates row-based access. A `CifLoopBlock` object can be
obtained by calling the `CifBlock` method `GetLoop(dataname)`.
Column-based access remains available for this object (e.g. `keys()`
returns a list of datanames in the loop and square bracket notation
returns a list of column values for that column).

A particular row can be selected using the `CifLoopBlock` 
`GetKeyedPacket` method:

~~~{.python}
    >>> lb = cf['testblock'].GetLoop('_item_6')
    >>> myrow = lb.GetKeyedPacket('_item_7','c') 
    >>> myrow._item_5
    '3'
~~~

In this example, the single packet with a value of `'c'` for `_item_7`
is returned, and packet values can then be accessed using the 
dataname as an attribute of the packet. Note that a `KeyError` is 
raised if more than one packet matches, or no packets match, and 
that the packet returned is a copy of the data read in from the 
file, and therefore can be changed without affecting the `CifBlock` 
object.

You may also access the nth value in this `CifLoopBlock`
object. ^[Warning: row and column order in a CIF loop is arbitrary;
while PyCIFRW currently maintains the row order seen in the input
file, there is nothing in the CIF standards which mandates this
behaviour, and later implementations may change this behaviour ], and
values can be obtained from these packets as attributes.

~~~{.python}
    >>> lb = cb.GetLoop("_item_5")
    >>> lb[0]
    ['1', 'a', '5']
    >>> lb[0]._item_7
    'a'
~~~

An alternative way of accessing loop data uses Python iterators, 
allowing the following syntax:

~~~{.python}
    >>> for a in lb: print `a["_item_7"]` 
    'a' 'b' 'c' 'd' 
~~~

Note that in both the above examples the row packet is a copy of 
the looped data, and therefore changes to it will not silently 
alter the contents of the original `CifFile` object, unlike the lists 
returned when column-based access is used.

### Changing or adding data values

If many operations are going to be performed on a single data 
block, it is convenient to assign that block to a new variable:

~~~{.python}
    cb = cf['my_block']
~~~

A new data name and value may be added, or the value of an 
existing name changed, by straight assignment:

~~~{.python}
    cb['_new_data_name'] = 4.5
    cb['_old_data_name'] = 'cucumber'
~~~

By default, old values are overwritten silently.  To instead 
raise an error when an item value is going to be overwritten,
set attribute 'overwrite' to `False`:

~~~{.python}
    cb.overwrite = False
    cb['_old_data_name'] = 'cucumber' # Error is raised
~~~

To return to the original behaviour, set `overwrite` to True.
To allow/disallow overwriting for all blocks in a file, call methods
unlock()/lock() respectively.

Note that values may be strings or numbers. 

#### Creating loops

To create a loop, simply set the column values to same-length lists,
and then call the `CifBlock` method `CreateLoop` with a list of the
looped datanames as a single argument.  This method will raise an
error if the datanames have different length columns assigned to them.
For example, the following commands create the example loop above:

~~~{.python}
    cb['_item_5']  = [1,2,3,4]
    cb['_item_7']  = ['a','b','c','d']
    cb['_item_6']  = [5,6,7,8]
    cb.CreateLoop(['_item_5','_item_7','_item_6'])
~~~

As a special case, if `CreateLoop` is called with data names that are
*not* list-valued, these items will be first placed into
single-element lists before creating the loop, resulting in a loop
with one row.

Another method, `AddToLoop(dataname,newdata)`, adds columns in
`newdata` to the pre-existing loop containing `dataname`, silently
overwriting duplicate data. `newdata` should be a Python dictionary of
dataname - datavalue pairs.

Note that lists (and other listlike objects except packets) 
returned by PyCIFRW actually point to the list currently inside 
the `CifBlock` object, and therefore any modification to them will 
modify the stored list. While this is often the desired 
behaviour, if you intend to manipulate such a list in other parts 
of your program while preserving the original CIF information, 
you should first copy the list to avoid destroying the loop 
structure:

~~~{.python}
    mysym = cb['_symmetry_ops'][:]
    mysym.append('x-1/2,y+1/2,z')
~~~

####  Changing item order

Item (and block) order has *no* semantic significance in CIF files.
However, the readability of CIF files in simple text editors leads to
a desire to organise the output order for human readers.  The
`ChangeItemOrder` method allows the order in which data items appear
in the printed file to be changed:

~~~{.python}
    mycif['testblock'].ChangeItemOrder('_item_5',0)
~~~

will move `_item_5` to the beginning of the datablock. When 
changing the order inside a loop block, the loop block's method 
must be called i.e.:

~~~{.python}
aloop = mycif['testblock'].GetLoop('_loop_item_1')
aloop.ChangeItemOrder('_loop_item_1',4)
~~~

Note also that the position of a loop within the file can be 
changed in this way as well, by passing the 'block number'
object as the first argument.  Each loop is assigned a simple
integer number, which can be found by calling `FindLoop` with
the name of a column in that loop:

~~~{.python}
loop_id = mycif['testblock'].FindLoop('_item_6')
mycif['testblock'].ChangeItemOrder(loop_id,0)
~~~

will move the loop block to the beginning of the printed 
datablock.

#### Adding and removing table rows

While it is most efficient to add columns to the `CifBlock` and then
bind them together once into a loop, it is possible to add a new row
into an existing loop using the `AddPacket(packet)` method of `CifLoopBlock`
objects:

~~~{.python}
    aloop = mycif['testblock'].GetLoop('_item_7')
    template = aloop.GetKeyedPacket('_item_7','d')
    template._item_5 = '5'
    template._item_7 = 'e'
    template._item_6 = '9'
    aloop.AddPacket(template)
~~~

Note we use an existing packet as a template in this example. If 
you wish to create a packet from scratch, you should instantiate 
a `StarPacket`:

~~~{.python}
    from CifFile import StarFile   #installed with PyCIFRW
    newpack = StarFile.StarPacket()
    newpack._item_5 = '5'  
    ...
    aloop.AddPacket(newpack)
~~~

Note that an error will be raised when calling `AddPacket` if the 
packet attributes do not exactly match the item names in the 
loop.

A packet may be removed using the `RemoveKeyedPacket` method, which 
chooses the packet to be removed based on the value of the given 
dataname: 

~~~{.python}
    aloop.RemoveKeyedPacket('_item_7','a')
~~~

## Writing CIF Files

The `CifFile` method `WriteOut` returns a string which may be passed 
to an open file descriptor:

~~~{.python}
    outfile = open("mycif.cif")
    outfile.write(cf.WriteOut())
~~~

Or the built-in Python `str()` function can be used:

    outfile.write(str(cf))

`WriteOut` takes an optional keyword argument, `comment`, which should be a 
string containing a comment which will be placed at the top of 
the output file. This comment string must already contain # 
characters at the beginning of lines:

~~~{.python}
    outfile.write(cf.WriteOut("#This is a test file"))
~~~

Two additional keyword arguments control line length in the output
file: `wraplength` and `maxoutlength`. Lines in the output file are
guaranteed to be shorter than `maxoutlength` characters, and PyCIFRW
will additionally insert a line break if putting two data values or a
dataname/datavalue pair together on the same line would exceed
`wraplength`. In other words, unless data values are longer than
`maxoutlength` characters long, no line breaks will be inserted into
those datavalues the output file. By default, `wraplength = 80` and
`maxoutlength = 2048`.  Note that the CIF line folding protocol is
used, which makes wrapping of long datavalues reversible.

These values may be set on a per block basis by calling the 
`SetOutputLength` method of the block.

The order of output of items within a `CifFile` or `CifBlock` is 
specified using the `ChangeItemOrder` method (see above). The 
default order is the order that items were first added in to 
the `CifFile`/`CifBlock`. Note that this order is not guaranteed
to be the order in which they appear in the input file.

### Templating system

If you want precise control of the layout of your CIF file, you can
pass a template file to the `CifBlock.process_template` method. A 
'template' is a CIF file containing a
single block, where the datanames are laid out in the way that the
user desires. The layout elements that are picked up from this template are:

1. order (overrides current order of `CifBlock`)
2. column position of datavalues (only the first row of a loop block is inspected) 
3. delimiters
4. If a semicolon-delimited string outside a loop contains 3 or more spaces in a row
   at the beginning of a line, that
   datavalue will be wrapped and indented by the same amount on output

Constraints on the template:

1. There should only ever be one dataname on each line
2.  `loop_` and and `datablock` tokens should appear as the only non-blank 
characters on their lines
3. Comments are flagged by a '#' as the first character in the line
4. Blank lines are acceptable (and ignored)
5. The dummy datavalues should use only alphanumeric characters
6. Semicolon-delimited strings are not allowed in loops

After calling `process_template` with the template file as the
argument, subsequent calls to `WriteOut` will respect the template
information, and revert to default behaviour for any datanames that
were not found in the template.  Templating is most useful when
formatting CIF dictionaries which are read heavily by
human readers, and have many (thousands!) of datablocks, each 
containing the same limited number of datanames.

#### Output format

CIF files are output by default in CIF2 grammar, but with the
CIF2-only triple quotes avoided unless explicitly requested through a
template.  Therefore, as long as CIF2-only datastructures (lists and
tables) are absent, the output CIF files will conform to 1.0,1.1 and
2.0 grammar.  The grammar of the output files can be changed by
calling `CifFile.set_grammar` with the choices being `1.0`,`1.1`,`2.0` or
`STAR2`.

## Deprecated classes

The ValidCifFile class is deprecated and will be removed in a future
version.

# Example programs

A program which uses PyCIFRW for validation, `validate_cif.py`, is 
included in the distribution in the `Programs` subdirectory. It 
will validate a CIF file (including dictionaries) against one or 
more dictionaries which may be specified by name and version or 
as a filename on the local disk. If name and version are 
specified, the IUCr canonical registry or a local registry is 
used to find the dictionary and download it if necessary.

## Usage

    python validate_cif.py [options] ciffile

## Options

    --version show version number and exit
    -h,--help print short help message
    -d dirname directory to find/store dictionary files
    -f dictname filename of locally-stored dictionary
    -u version dictionary version to resolve using registry
    -n name dictionary name to resolve using registry
    -s store downloaded dictionary locally (default True)
    -c fetch and use canonical registry from IUCr
    -r registry location of registry as filename or URL
    -t The file to be checked is itself a DDL2 dictionary

# Further information

The source files are in a literate programming format (noweb) 
with file extension .nw. HTML documentation generated from these 
files and containing both code and copious comments is included 
in the downloaded package. Details of interpretation of the 
current standards as relates to validation can be found in these 
files.