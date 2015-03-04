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
