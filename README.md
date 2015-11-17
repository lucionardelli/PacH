# PacH 
=======
**Lucio Nardelli - _Director_ Hernán Ponce de León**

### Description

 Parse logs (as .xes or .txt Files) and calculate the minimum convex hull using Pyhull (https://pythonhosted.org/pyhull)
 of the  Parikh's vector of the the events in the traces.

 We use two different high-level techniques to handle large logs: projection and sampling

 After getting the convex hull, some automatic simplifications are made in order to get a "nicer" model.
 
 As a final step, the resuilting PNML is generated according to the international standard.
 
###Installation
 In order to use it, some requirements are that must be met.
 It can be done via Pip:
        
      pip install -r requirements.txt

 or see the file `requirements.txt` for an exahustive list or dependencies.

###Contents and Usage

#####`parser.py`

Used for parsing the log file and get the Parikh's vector representation of the traces.

**Usage**:

    ./parser.py <LOG filename> [--verbose]

If `--verbose` is no used, just a summary is printed. Otherwise  a full representation of the traces will we printed to the standard output.

#####`negative_parser.py`

Similar to the previous, but only the full trace is converted to a Parikh's vector, not the prefixes.

**Usage**:

    ./negative_parser.py <negative XES LOG filename> [--verbose]

#####`qhull.py`

Search, representation and simplification of a Convex Hull.
Points can be a list of lists or a file with the list of lists as the first line of it.

**Usage**:

    Usage: ./qhull.py <points> [--debug][--verbose]

#####`pach.py`

A wrape up of the elements necesary for:

  - Parsing
  - Getting the convex hull
  - Applying the automatic simplifications w.r.t. the negative traces
  -Generation of the Petri Net according to the *Petri Net Makup Language* (PNML http://www.pnml.org/)
  - Generation of an output file fof performance statistics.

**Usage**:

    Usage: ./pach.py <LOG_filename> [--debug][--verbose]
    [--negative <Negative points filename>] [max_coeficient]]
    [--sampling [<number of samplings>] [<sampling size>]]
    [--projection [<max group size>] [<connected model>]]
    [--smt-matrix [<timeout>]]
    [--smt-iter [<timeout>]]
    [--sanity-check]

**_Arguments_**:

  - LOG_filename : The file where te positive log is
  - ` --debug ` : Open a Python Debugger just before calling PacH
  - ` --verbose`: Verbose mode.
  - `--negative`
    - Negative_points_filename> 
    - `[max_coeficient]`: Optional argument. Only try to remove facets whith at least one coefficient bigger than max_coefficient.
  - `--sampling` : Whether to do sampling or not
    - `number of samplings`:  Number of samples to get
    - `sampling size`: The size of each sample
  - `--projection`: Whether to do projection or not
    - `[max group size]`: Maximum number of dimension in each cluster
    - `[connected model]`: Whether to connect the cluster or not
  - `--smt-matrix`: Matrix simplification of all the ecuations system at once
    - ` [timeout]`: Optional argument to set a timeout for SMT simplification
  - `--smt-iter`:  SMT simplification to each indiviual facet of the convex hull
    - ` [timeout]`: Optional argument to set a timeout for SMT simplification
  - `--sanity-check`: Perform some sanity check after each new hull.

**_Output_**:

  The programm will generate two files.

  - PNML representation of the simplified convex hull. 
  - A file with a summary and performance details
    - Example of output file:

`

    Statistic of {positive}: with negative traces from {negative}
    benchmark       ->  {benchmark }
    positive        ->  {positive traces file}
    dimension       ->  {dimension}
    traces          ->  {positive traces}
    events          ->  {total events found in positive traces}
    negative        ->  {negative traces file}
    complexity      ->  {complexity of the model}  
    exec_time       ->  {execution time}
    overall_time    ->  {overall time}
    details
        parse_traces    ->  {time parsing traces}
        parse_negatives ->  {time parsing negatives}
        do_sampling     ->  {time doing sampling}
        do_projection   ->  {time doing projection}
        convexHull      ->  {time computing hiperspaces}
        shift&rotate    ->  {time simplifying hull with SMT} OR {Time simplifying each facet with SMT}
        simplify        ->  {Time spent simplifying without SMT}

`

#####`comparator.py`

Experimental tool to compare all 3 simplifications w.r.t. a unique convex hull representation.


**Usage**:

    Usage: ./comparator.py <LOG filename> [--debug]
    [--negative <Negative points filename>] [max_coeficient]]
    [--sampling [<number of samplings>] [<sampling size>]]
    [--projection [<max group size>] [<connected model>]]
    [--smt-matrix [<timeout>]]
    [--smt-iter [<timeout>]]

**_Arguments_**:

Analogous to the ones of `pach.py`.
