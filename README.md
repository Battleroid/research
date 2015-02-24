# research
Research material for senior project.

## instructions

Run `python manager.py` to start menu for splitting/viewing information. You can also do the same with `python master.py filename.npz` for a regular split or `python master.py filename.npz true` to perform a master split.

## restrictions

Currently only works on Numpy archives (npz). Eventually will need to introduce a script to convert between csv/tsv possibly, depends on how the data I need is given to me.

## basic help for `manager.py`

* `s i` -- will split entry i
* `sf name` -- will perform a master split on a filename (only use this for the master split!)
* `db c` -- creates tables for database
* `db d` -- deletes tables for database
* `db reset` -- performs `db d` then `db c`, alias essentially
* `burn` -- destroys all files associated with database, then resets the database
* `help` -- prints help information
* `exit` -- exits manager

## todo

* Currently it works as expected with the exception of one issue. During `create_p()` in `master.py` if it encounters a ZeroDivisionError it cancels out which in the previous `rm.py` it passed correctly (and simply left it as 0). However, it is not being skipped over as expected, need to find out why.
* Conversion script to convert data to npz.
* Command line options/functions so you can possibly skip starting `manager.py` to reset the DB or do the master split.
* Possibly way to view the A for each `g*` group.
* Probably not needed, but possibly a way to view the parent/children of a particular node (think like a tree view).
* Need way to protect user from accidentally performing master split on non-master items.
* I think adding another field to the database to just hold the size of the array (think 25x25, 5x5, etc) would be helpful. Would prevent needless attempts at splitting matrices that are too small.
* Need way to confirm actions for `db` and `burn`! Possibly decorator function?
* Do some clean up and use `isdigit()` instead of a bunch of ValueErrors (can't believe I forget that simple junk).
