__author__ = 'Casey Weed'
__version__ = 'v1.0'

from cmd import Cmd
from texttable import Texttable
import numpy as np
import os
from peewee import DoesNotExist
import master
from files import File, database as db

class AlreadyProcessed(Exception):
    def __init__(self, message=None):
        if not message:
            self.message = 'Matrix already processed, cannot reprocess.'
        self.message = message

def partition(idx, SHAPE_THRESHOLD=5, Q_THRESHOLD=0.0, GT_THAN_ZERO=True):
    try:
        parent = File.get(id=idx)
        if parent.processed:
            raise AlreadyProcessed
        if SHAPE_THRESHOLD >= parent.shape:
            raise master.CannotSplit(message='Matrix cannot be split, exceeds threshold of %dx%d.' % (SHAPE_THRESHOLD, SHAPE_THRESHOLD))
        print 'Splitting %s' % parent.filename
        f1, f2 = master.split('.'.join((parent.filename, parent.ext)))
        if GT_THAN_ZERO:
            if not f1.q > Q_THRESHOLD or not f2.q > Q_THRESHOLD:
                raise master.CannotSplit(message='Matrix cannot be split, exceeds Q threshold of %d.' % Q_THRESHOLD)
        else:
            if f1.q <= Q_THRESHOLD or f2.q <= Q_THRESHOLD:
                raise master.CannotSplit(message='Matrix cannot be split, exceeds Q threshold of %d.' % Q_THRESHOLD)
        File.create(parent=parent.id, filename=f1.filename, ext=f1.ext, q=f1.q, shape=f1.shape, a_elems=f1.a_elems)
        File.create(parent=parent.id, filename=f2.filename, ext=f2.ext, q=f2.q, shape=f2.shape, a_elems=f2.a_elems)
    except DoesNotExist:
        print 'ID %d does not exist!' % idx
    except AlreadyProcessed:
        print 'Cannot split %d, it has already been processed.' % idx
    except ZeroDivisionError:
        pass
    except master.CannotSplit, e:
        parent.leaf = True
        print e.message
    finally:
        parent.processed = True
        parent.save()

def saveall(directory='results', leaves_only=True):
    if not os.path.exists(directory):
        os.mkdir(directory)
    if leaves_only:
        filenames = {f.filename: '.'.join((f.filename, f.ext)) for f in File.select().where(File.leaf == True).iterator()}
    else:
        filenames = {f.filename: '.'.join((f.filename, f.ext)) for f in File.select().where(File.processed == True).iterator()}
    for key, val in filenames.iteritems():
        fn = '.'.join((key, 'txt'))
        print 'Saving %s as %s' % (key, os.path.join(directory, fn))
        data = np.load(val)
        a = data['a']
        q = data['q']
        a_elems = data['a_elems']
        shape = len(a_elems)
        with open(os.path.join(directory, fn), 'w') as f:
            # header
            f.write('# name: %s, total elements: %d, q: %.64f%s' % (key, shape, q, os.linesep))
            for idx, row in enumerate(a):
                # bitstring
                line = '%04d: %s%s' % (a_elems[idx], ''.join(map(str, row)), os.linesep)
                f.write(line)
    print 'Finished'

def partitionall(SHAPE_THRESHOLD=5, Q_THRESHOLD=0.0):
    if [x.processed for x in File.select().where(File.processed == False).iterator()]:
        [partition(z.id, SHAPE_THRESHOLD, Q_THRESHOLD) for z in File.select().where(File.processed == False).iterator()]
    if [x.processed for x in File.select().where(File.processed == False).iterator()]:
        return partitionall(SHAPE_THRESHOLD, Q_THRESHOLD)
    else:
        print 'Finished'
        return

def view(idx):
    try:
        idx = int(idx)
        target = File.get(id=idx)
        data = np.load('.'.join((target.filename, target.ext)))
        print 'Matrix %s:%s%s%s' % (target.filename, os.linesep, data['a'], os.linesep)
        print 'Origin elements:%s%s%s ' % (os.linesep, ', '.join(map(str, data['a_elems'])), os.linesep)
        parent_id = target.parent.id
        print 'Parent of %i is %i.' % (idx, parent_id)
    except DoesNotExist:
        print 'ID %d does not exist!' % idx
    except AttributeError:
        print 'No parent could be found (possible that this is the master split).'

def burn():
    file_list = ['.'.join((i.filename, i.ext)) for i in File.select()]
    if not file_list:
        print 'Database empty, skipping.'
        return 
    for f in file_list:
        if os.path.exists(f):
            print 'Removing %s' % f
            os.remove(f)
    print 'Resetting database.'
    reset_database()

def create_table():
    db.connect()
    db.create_table(File)

def drop_tables():
    db.connect()
    db.drop_table(File)

def reset_database():
    drop_tables()
    create_table()

def check_database():
    if not File.table_exists():
        create_table()
        return True
    else:
        return False

def menu(leaves_only=False):
    if leaves_only:
        query = File.select().where(File.leaf == True)
    else:
        query = File.select()
    table = Texttable()
    headers = ['ID', 'Used', 'Name', 'Q', 'Shape']
    rows = [[a.id, 'x' if a.processed else '', a.filename, a.q, a.shape] for a in query]
    align = ['r', 'r', 'l', 'r', 'r']
    rows.insert(0, headers)
    table.add_rows(rows)
    table.set_cols_align(align)
    table.set_deco(Texttable.HEADER)
    print table.draw()

class Manager(Cmd):

    NUMPY_LW = 80
    NUMPY_THRESHOLD = 80
    VIEW_ONLY_LEAVES = False
    SHAPE_THRESHOLD = 5
    Q_THRESHOLD = 0
    SHOW_MENU_AFTER_CMD = False
    GT_THAN_ZERO = True

    prompt = 'Manager> '
    ruler = '-'

    def _set_numpy(self, val):
        np.set_printoptions(threshold=val)

    def _set_numpy_lw(self, val):
        np.set_printoptions(linewidth=val)

    def help_save_all(self):
        print 'Save all nodes to text files. Default directory is \'results\'. \
Use toggle_leaves to toggle saving only the leaves of the tree.'

    def do_save_all(self, line):
        if not line:
            saveall(leaves_only=self.VIEW_ONLY_LEAVES)
            return
        line = line.split()
        directory = line[0]
        if not os.path.exists(directory):
            print '%s does not exist!' % directory
            return
        saveall(directory, leaves_only=self.VIEW_ONLY_LEAVES)

    def help_set_q(self):
        print 'Set Q threshold. Current is %.8f.' % self.Q_THRESHOLD

    def do_set_q(self, line):
        if not line:
            print 'Q threshold set to %.8f.' % self.Q_THRESHOLD
            return
        try:
            new_q = float(line)
            self.Q_THRESHOLD = new_q
            print 'Q Threshold set to %.8f.' % new_q
        except ValueError:
            print '%s is not a float.' % line
            return

    def help_set_numpy_lw(self):
        pass

    def do_set_numpy_lw(self, line):
        if not line:
            print 'Numpy line width set to %i.' % self.NUMPY_LW
            return
        try:
            new_numpy_lw = int(line.strip())
            self._set_numpy_lw(line)
            print 'Numpy line width set to %i.' % new_numpy_lw
        except ValueError:
            print '%s is not an integer.' % line
            return

    def help_set_numpy(self):
        print 'Set Numpy threshold. Current is %i.' % self.NUMPY_THRESHOLD

    def do_set_numpy(self, line):
        if not line:
            print 'Numpy threshold set to %i.' % self.NUMPY_THRESHOLD
            return
        try:
            new_numpy = int(line)
            if not new_numpy > 0:
                print 'Numpy threshold must be greater than 0.'
                return
            self.NUMPY_THRESHOLD = new_numpy
            self._set_numpy(np.nan)
            print 'Numpy threshold set to %i.' % new_numpy
        except ValueError:
            print '%s is not an integer.' % line
            return

    def help_set_shape(self):
        print 'Set shape threshold. Current is %i.' % self.SHAPE_THRESHOLD

    def do_set_shape(self, line):
        if not line:
            print 'Shape threshold set to %i.' % self.SHAPE_THRESHOLD
            return
        try:
            new_threshold = int(line)
            self.SHAPE_THRESHOLD = new_threshold
            print 'Threshold set to %i' % self.SHAPE_THRESHOLD
        except ValueError:
            print '%s is not an integer.' % line
            return

    def help_view(self):
        print 'View node information of specified ID.'

    def do_view(self, line):
        line = line.split()
        if not line:
            print 'Missing arguments.'
            return
        idx = int(line[0])
        view(idx)

    def help_convert_text(self):
        print 'Convert text file with bitstrings to compressed Numpy archive (.npz) ready for splitting. Specify \'blank\' \
to remove empty (zero only) rows/cols from matrix before saving. Sample usage: file.txt [blank].'

    def do_convert_text(self, line):
        line = line.split()
        if not line:
            print 'Missing arguments.'
            return
        target = line[0]
        blank = False
        if not os.path.exists(target):
            print '%s does not exist!' % target
            return
        if len(line) > 1:
            if line[1].lower() == 'blank':
                blank = True
        master.loadtxt(target, blank=blank)

    def complete_convert_text(self, text, line, begidx, endidx):
        if not text:
            completions = [f for f in os.listdir('.')]
        else:
            completions = [f for f in os.listdir('.') if f.startswith(text) and f.endswith('.txt')]
        return completions

    def help_load(self):
        print 'Load specified Numpy compressed archive (.npz) and perform split, \
use \'yes\' to do initial split. Sample usage: file.npz [yes].'

    def do_load(self, line):
        line = line.split()
        if not line:
            print 'Missing arguments.'
            return
        target = line[0]
        initial = False
        if not os.path.exists(target):
            print '%s does not exist!' % target
            return
        if len(line) > 1:
            if line[1].lower() == 'yes':
                initial = True
        master.split(target, initial=initial)

    def complete_load(self, text, line, begidx, endidx):
        if not text:
            completions = [f for f in os.listdir('.')]
        else:
            completions = [f for f in os.listdir('.') if f.startswith(text) and f.endswith('.npz')]
        return completions

    def help_burn_database(self):
        print 'Reset database and clear all files associated with the nodes in the database.'

    def do_burn_database(self, line):
        burn()

    def help_reset_database(self):
        print 'Reset the database, but do not clear files.'

    def do_reset_database(self, line):
        reset_database()

    def help_split_all(self):
        print 'Continuously split all records until all have been processed.'

    def do_split_all(self, line):
        partitionall(self.SHAPE_THRESHOLD, self.Q_THRESHOLD)

    def help_split(self):
        print 'Split record i, or a list of records using comma delimited list (ex: 1,3,4).'

    def do_split(self, line):
        if not line:
            print 'Missing arguments.'
            return
        try:
            idxs = [int(i) for i in line.split(',')]
            [partition(i, self.SHAPE_THRESHOLD, self.Q_THRESHOLD) for i in idxs]
        except ValueError:
            print 'Invalid arguments.'

    def help_menu(self):
        print 'Show menu of IDs and other information for nodes.'

    def do_menu(self, line):
        menu(self.VIEW_ONLY_LEAVES)

    def help_toggle_leaves(self):
        print 'Toggles listing only leaves in the menu. Currently set to %s.' % ('on' if self.VIEW_ONLY_LEAVES else 'off')

    def do_toggle_leaves(self, line):
        self.VIEW_ONLY_LEAVES = not self.VIEW_ONLY_LEAVES
        print 'Leaves only mode is %s.' % ('off' if not self.VIEW_ONLY_LEAVES else 'on')

    def help_toggle_menu(self):
        print 'Toggles showing the menu after execution of commands. Currently set to %s.' % ('on' if self.SHOW_MENU_AFTER_CMD else 'off')

    def do_toggle_menu(self, line):
        self.SHOW_MENU_AFTER_CMD = not self.SHOW_MENU_AFTER_CMD
        print 'Menu is now toggled %s.' % ('off' if not self.SHOW_MENU_AFTER_CMD else 'on')

    def help_toggle_gt(self):
        print 'Toggles how to check for Q. Currently set to %s.' % ('>' if self.GT_THAN_ZERO else '<=')

    def do_toggle_gt(self, line):
        self.GT_THAN_ZERO = not self.GT_THAN_ZERO
        print 'Now checking for Q %s 0.' % ('>' if self.GT_THAN_ZERO else '<=')

    def do_EOF(self, args):
        return self.do_exit(args)

    def do_exit(self, args):
        return True

    def preloop(self):
        if check_database():
            print 'Database created.'
        else:
            print 'Database already exists, good to go.'
        self._set_numpy(self.NUMPY_THRESHOLD)
        self._set_numpy_lw(self.NUMPY_LW)

    def postcmd(self, stop, line):
        if self.SHOW_MENU_AFTER_CMD:
            menu(self.VIEW_ONLY_LEAVES)
        if stop:
            return True

if __name__ == '__main__':
    Manager().cmdloop(intro='Manage the splitting of data sets.')