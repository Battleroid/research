# research
Research material for senior project.

## instructions

Run `python manager.py` to start menu for splitting/viewing information. You can also do the same with `python master.py filename.npz` to manually split.

## restrictions

Currently only works on Numpy archives (npz). Eventually will need to introduce a script to convert between csv/tsv possibly, depends on how the data I need is given to me.

## todo

* Currently it works as expected with the exception of one issue. During `create_p()` in `master.py` if it encounters a ZeroDivisionError it cancels out which in the previous `rm.py` it passed correctly (and simply left it as 0). However, it is not being skipped over as expected, need to find out why.
* Conversion script to convert data to npz.
* Command line options/functions so you can possibly skip starting `manager.py` to reset the DB or do the master split.
* Possibly way to view the A for each `g*` group.
* Probably not needed, but possibly a way to view the parent/children of a particular node (think like a tree view).
