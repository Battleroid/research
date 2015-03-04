# research
Research material for senior project.

## instructions

Run `python manager.py` to start menu for splitting/viewing information. You can also do the same with `python master.py filename.npz` for a regular split or `python master.py filename.npz true` to perform a master split.

## restrictions

Works on numpy archives (npz), will load basic bitstrings from text files.

## basic help for `manager.py`

* `s i` -- split matrix i
* `sr i-j` -- split nodes i through j
* `ss i,j,k` -- split a list of nodes with a comma delimiter
* `sall` -- recursively partition until all values are false
* `v i` -- view matrix information of i, if it has a parent it is viewable as well
* `tl` -- toggle leaves only mode
* `sf name` -- split data stored in 'name', use only for first split
* `lt name` -- load text file and split
* `db c` -- create tables for database manually
* `db d` -- drop tables for database manually
* `db reset` -- perform both 'db d' and 'db c'
* `burn` -- removes all files associated with database
* `npt` -- unlock numpy threshold
* `shape` -- change shape threshold (default 5)
* `qth` -- change q threshold (default 0)
* `help` -- print this information
* `exit` -- exit the manager

## todo

* Command line options/functions so you can possibly skip starting `manager.py` to reset the DB or do the master split.
* Do some clean up and use `isdigit()` instead of a bunch of ValueErrors (can't believe I forget that simple junk).
* Need clarification on [checking the thresholds][threshold]. If I check both the shape and Q beforehand it pretty stops immediately at the beginning because both of Qs from the master splits are below zero. However, if I only check the Qs of the splits, it performs fine. Question is: should I check the Q before splitting? Or should I only check the Qs of the splits and cancel the split if either is beyond the threshold, or should I only abandon the group that did not fit the threshold? Either are easily doable, just need to know which is what is needed.

[threshold]: https://github.com/Battleroid/research/blob/master/manager.py#L84-L96
