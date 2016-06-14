# PacH 
=======
**Lucio Nardelli - _Director_ Hernán Ponce de León**

### Description

 Parse logs (as .xes or .txt Files) and calculate the minimum convex hull using Pyhull (https://pythonhosted.org/pyhull)
 of the  Parikh's vector of the the events in the traces.

 We use two different high-level techniques to handle large logs: projection and sampling

 After getting the convex hull, some automatic simplifications are made in order to get a "nicer" model.
 
 As a final step, the resulting PNML is generated according to the international standard.
 
###Installation
 In order to use it, some requirements are that must be met.
 It can be done via Pip:
        
      pip install -r requirements.txt

 or see the file `requirements.txt` for an exhaustive list or dependencies.

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

A wrap up of the elements necessary for:

  - Parsing
  - Getting the convex hull
  - Applying the automatic simplifications w.r.t. the negative traces
  -Generation of the Petri Net according to the *Petri Net Markup Language* (PNML http://www.pnml.org/)
  - Generation of an output file of performance statistics.

**Usage**:

    Usage: ./pach.py <LOG_filename> [--debug][--verbose]
    [--negative <Negative points filename>] [max_coefficient]]
    [--sampling [<number of samplings>] [<sampling size>]]
    [--projection [<max group size>] [<connected model>]]
    [--smt-matrix [<timeout>]]
    [--smt-iter [<timeout>]]
    [--sanity-check]

**_Arguments_**:

  - LOG_filename : The file where the positive log is
  - ` --debug ` : Open a Python Debugger just before calling PacH
  - ` --verbose`: Verbose mode.
  - `--negative`
    - Negative_points_filename> 
    - `[max_coefficient]`: Optional argument. Only try to remove facets with at least one coefficient bigger than max_coefficient.
  - `--sampling` : Whether to do sampling or not
    - `number of samplings`:  Number of samples to get
    - `sampling size`: The size of each sample
  - `--projection`: Whether to do projection or not
    - `[max group size]`: Maximum number of dimension in each cluster
    - `[connected model]`: Whether to connect the cluster or not
  - `--smt-matrix`: Matrix simplification of all the equations system at once
    - ` [timeout]`: Optional argument to set a timeout for SMT simplification
  - `--smt-iter`:  SMT simplification to each individual facet of the convex hull
    - ` [timeout]`: Optional argument to set a timeout for SMT simplification
  - `--sanity-check`: Perform some sanity check after each new hull.

**_Output_**:

  The program will generate two files.

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
        convexHull      ->  {time computing hyperspaces}
        shift&rotate    ->  {time simplifying hull with SMT} OR {Time simplifying each facet with SMT}
        simplify        ->  {Time spent simplifying without SMT}

`

#####`comparator_xes.py`

Tool to compare all 3 simplifications (Polyhedra, STM-Matrix, SMT-Iterative) w.r.t. a unique convex hull representation.


**Usage**:

    Usage: ./comparator_xes.py <LOG filename> [--debug]
    [--negative <Negative points filename>] [max_coefficient]]
    [--sampling [<number of samplings>] [<sampling size>]]
    [--projection [<max group size>] [<connected model>]]
    [--smt-matrix [<timeout>]]
    [--smt-iter [<timeout>]]


    If using config file, this are the options
        samp_num :  Number of samples to take (Default no sample, use all elements)
        nfilename :    Negative traces file location
        max_coef :    Maximum allowed in halfspaces. If no coefficient is bigger than this, won't try to simplify
        proj_size :    Number for maximum dimension to project to (Default no projection, 0 for no limit)
        proj_connected :    Boolean indicating whether to (try to) connect clusters (default: True)
        smt_timeout_matrix :    Timeout for smt solution finding when simplifying all hull at once
        samp_size :    Number of elements to take on each sample (No default)
        sanity_check :    Performs sanity check that all traces are inside hull
        smt_timeout_iter :    Timeout for smt solution finding when simplifying one halfspace at the time
        filename :    Location of .xes file with traces or .pnml file with Petri net model


**_Arguments_**:

Analogous to the ones of `pach.py`.

#####`comparator_pnml.py`

Tool to compare all 3 simplifications (Polyhedra, STM-Matrix, SMT-Iterative) applied to ProM/ILPMiner output.

**Usage**:

    Usage: ./comparator_pnml.py <PNML filename> [--debug]
    [--negative <Negative XES points filename>] [max_coefficient]]
    [--smt-matrix [<timeout>]]
    [--smt-iter [<timeout>]]


    If using config file, this are the options
        samp_num :  Number of samples to take (Default no sample, use all elements)
        nfilename :    Negative traces file location
        max_coef :    Maximum allowed in halfspaces. If no coefficient is bigger than this, won't try to simplify
        proj_size :    Number for maximum dimension to project to (Default no projection, 0 for no limit)
        proj_connected :    Boolean indicating whether to (try to) connect clusters (default: True)
        smt_timeout_matrix :    Timeout for smt solution finding when simplifying all hull at once
        samp_size :    Number of elements to take on each sample (No default)
        sanity_check :    Performs sanity check that all traces are inside hull
        smt_timeout_iter :    Timeout for smt solution finding when simplifying one halfspace at the time
        filename :    Location of .xes file with traces or .pnml file with Petri net model


**_Arguments_**:

Analogous to the ones of `pach.py`.
