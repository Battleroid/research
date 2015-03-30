__author__ = 'Casey Weed'
__version__ = '1.2'
__intro__ = """
    __  ___
   /  |/  /___ _____  ____ _____ ____  _____
  / /|_/ / __ `/ __ \/ __ `/ __ `/ _ \/ ___/
 / /  / / /_/ / / / / /_/ / /_/ /  __/ /
/_/  /_/\__,_/_/ /_/\__,_/\__, /\___/_/
                         /____/
version %s""" % __version__

from cmd import Cmd
from texttable import Texttable
import numpy as np
import os
from peewee import DoesNotExist
from research.files import File, Item, database as db
from research import master

class AlreadyProcessed(Exception):
    def __init__(self, message=None):
        if not message:
            self.message = 'Matrix already processed, cannot reprocess.'
        self.message = message

def partition(idx, shape_threshold=5, q_threshold=0.0, gt_than_zero=True):
    try:
        parent = File.get(id=idx)
        # check processed
        if parent.processed:
            raise AlreadyProcessed
        # check shape
        if shape_threshold >= parent.shape:
            raise master.CannotSplit(message='Matrix cannot be split, exceeds threshold of %ix%i.' % (shape_threshold, shape_threshold))
        print 'Splitting %s' % parent.filename
        f1, f2 = master.split('.'.join((parent.filename, parent.ext)))
        # create records
        z1 = File(parent=parent.id, filename=f1.filename, ext=f1.ext, q=f1.q, shape=f1.shape, a_elems=f1.a_elems)
        z2 = File(parent=parent.id, filename=f2.filename, ext=f2.ext, q=f2.q, shape=f2.shape, a_elems=f2.a_elems)
        # check q
        if gt_than_zero:
            if not f1.q > q_threshold or not f2.q > q_threshold:
                raise master.CannotSplit(message='Matrix cannot be split, exceeds Q threshold of %f.' % q_threshold)
        else:
            if f1.q <= q_threshold or f2.q <= q_threshold:
                raise master.CannotSplit(message='Matrix cannot be split, exceeds Q threshold of %f.' % q_threshold)
        # save file records
        z1.save()
        z2.save()
    except DoesNotExist:
        print 'ID %i does not exist!' % idx
    except AlreadyProcessed:
        print 'Cannot split %i, it has already been processed.' % idx
    except ZeroDivisionError:
        pass
    except master.CannotSplit, e:
        parent.leaf = True
        print e.message
    finally:
        parent.processed = True
        parent.save()

def save_all(directory='results', leaves_only=True, summary=False):
    if not os.path.exists(directory):
        os.mkdir(directory)
    if leaves_only:
        filenames = {f.filename: '.'.join((f.filename, f.ext)) for f in File.select().where(File.leaf == True).iterator()}
    else:
        filenames = {f.filename: '.'.join((f.filename, f.ext)) for f in File.select().where(File.processed == True).iterator()}
    leaves = dict()
    for key, val in filenames.iteritems():
        fn = '.'.join((key, 'txt'))
        print 'Saving %s as %s' % (key, os.path.join(directory, fn))
        data = np.load(val)
        a = data['a']
        q = data['q']
        a_elems = data['a_elems']
        shape = len(a_elems)
        original_size = data['original_size']
        # change shape to something configurable
        leafstring = np.zeros(original_size, dtype=np.int)
        for i in a_elems:
            leafstring[i] = 1
        leafstring_str = ''.join(map(str, leafstring))
        leaves[key] = leafstring_str
        with open(os.path.join(directory, fn), 'w') as f:
            # header
            f.write('# name: %s, total elements: %i, q: %.5f%s' % (key, shape, q, os.linesep))
            for idx, row in enumerate(a):
                # bitstring
                row_str = ''.join(map(str, row))
                line = '%04d: %s%s' % (a_elems[idx] + 1, row_str, os.linesep)  # increase elem num by 1 for readability
                f.write(line)
            # leafstring
            f.write('%s' % leafstring_str)
    if summary:
        tree_summary(os.path.join(directory, 'summary.txt'))
        print 'Leafstring summary included!'
    print 'Finished'

def partition_all(shape_threshold=5, q_threshold=0.0):
    if [x.processed for x in File.select().where(File.processed == False).iterator()]:
        [partition(z.id, shape_threshold, q_threshold) for z in File.select().where(File.processed == False).iterator()]
    if [x.processed for x in File.select().where(File.processed == False).iterator()]:
        return partition_all(shape_threshold, q_threshold)
    else:
        print 'Finished'
        return

def tree_summary(filename, Q_THRESHOLD, SHAPE_THRESHOLD, GT_THAN_ZERO):
    query = File.select().where(File.parent == None).iterator()
    with open(filename, 'w') as f:
        for idx, root in enumerate(query):
            if idx:
                f.write(os.linesep)
            node_summary(root, f, Q_THRESHOLD, SHAPE_THRESHOLD, GT_THAN_ZERO)
    print 'Finished'

class Reason(object):
    '''Contain the reasons why, probably unnecessary. Please come back and fix someday.'''
    def __init__(self):
        self.parent = []
        self.g1 = []
        self.g2 = []

def node_summary(node, f, Q_THRESHOLD, SHAPE_THRESHOLD, GT_THAN_ZERO):
    # create primitive string for indent to show structure
    indent = get_indent(node) * 2
    ind_str = ''
    for i in range(indent):
        if i % 2 == 0:
            ind_str += '|'
        else:
            ind_str += '-'
    # create info text
    info = '%s (shape=%i, q=%.5f)' % (node.filename, node.shape, node.q)
    tmp_g1_info = ''
    tmp_g2_info = ''
    # indicate whether or not it is a leaf or has children (:)
    if node.leaf:
        info += ' is leaf'
    else:
        info += ':'
    # let's just get the info, at this point I just want it to work, some other day I can come back and fix it up nice
    # and neat
    if node.leaf:
        # get reasons for why the leaf is a leaf
        reasons = Reason()
        # parent reasons
        if node.shape <= SHAPE_THRESHOLD:
            reasons.parent.append('Shape exceeds threshold.')
        # tmp g1/g2 temp split, not saved, just gives me the stats of each split, don't even care
        # about if the shape is too small or q too small, it doesn't matter, we're not saving it
        tmp_g1, tmp_g2 = master.temp_split('.'.join((node.filename, node.ext)))
        # tmp g1 shape & q checks
        if tmp_g1.shape <= SHAPE_THRESHOLD:
            reasons.g1.append('Shape exceeds threshold')
        if GT_THAN_ZERO:
            if not tmp_g1.q > Q_THRESHOLD:
                reasons.g1.append('Q exceeds threshold')
        else:
            if tmp_g1 <= Q_THRESHOLD:
                reasons.g1.append('Q exceeds threshold')
        # tmp g2 shape & q checks
        if tmp_g2.shape <= SHAPE_THRESHOLD:
            reasons.g2.append('Shape exceeds threshold')
        if GT_THAN_ZERO:
            if not tmp_g2.q > Q_THRESHOLD:
                reasons.g2.append('Q exceeds threshold')
        else:
            if tmp_g2 <= Q_THRESHOLD:
                reasons.g2.append('Q exceeds threshold')
        # set info lines
        tmp_g1_info = ind_str + '|-%s (shape=%i, q=%.5f) %s %s' % (tmp_g1.filename, tmp_g1.shape, tmp_g1.q, 'not saved due to:' if reasons.g1 else 'not saved due to %s' % tmp_g2.filename, ', '.join(reasons.g1))
        tmp_g2_info = ind_str + '|-%s (shape=%i, q=%.5f) %s %s' % (tmp_g2.filename, tmp_g2.shape, tmp_g2.q, 'not saved due to:' if reasons.g2 else 'not saved due to %s' % tmp_g1.filename, ', '.join(reasons.g2))
        # set parent if it has anything to add (which is just the shape)
        if reasons.parent:
            info += ' not split due to: %s' % ', '.join(reasons.parent)  # is this needed?
    # write line
    if node.leaf:
        # write line and the additional tmp split info
        line = ''.join((ind_str, info, os.linesep, tmp_g1_info, os.linesep, tmp_g2_info))
        f.write(''.join((line, os.linesep)))
    else:
        # only write line info
        line = ''.join((ind_str, info))
        f.write(''.join((line, os.linesep)))
    # if the node has children, repeat the process on each child
    if node.children:
        for child in node.children:
            node_summary(child, f, Q_THRESHOLD, SHAPE_THRESHOLD, GT_THAN_ZERO)

def get_indent(node, level=0):
    if node.parent:
        level += 1
        return get_indent(node.parent, level)
    return level

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
    file_list = Item.select().iterator()
    if not file_list:
        print 'Database empty, skipping.'
        return 
    for f in file_list:
        if os.path.exists(f.filename):
            print 'Removing %s' % f.filename
            os.remove(f.filename)
    print 'Resetting database.'
    reset_database()

def create_table():
    db.connect()
    db.create_tables([File, Item])

def drop_tables():
    db.connect()
    db.drop_tables([File, Item])

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
    print '%i leaves of %i total records.' % (query.count() if leaves_only else
                                              File.select().where(File.leaf == True).count(),
                                              File.select().count())
    print table.draw()

class Manager(Cmd):

    NUMPY_LW = 80
    NUMPY_THRESHOLD = 80
    Q_THRESHOLD = 0
    SHAPE_THRESHOLD = 5
    GT_THAN_ZERO = True
    SHOW_MENU_AFTER_CMD = False
    VIEW_ONLY_LEAVES = False

    prompt = 'Manager> '
    ruler = '-'

    def do_tree_summary(self, line):
        if not File.select().count():
            print 'Database empty, nothing to summarize.'
            return
        line = line.split()
        if line:
            filename = line[0]
            tree_summary(filename, self.Q_THRESHOLD, self.SHAPE_THRESHOLD, self.GT_THAN_ZERO)
        else:
            tree_summary('summary.txt', Q_THRESHOLD=self.Q_THRESHOLD, SHAPE_THRESHOLD=self.SHAPE_THRESHOLD, GT_THAN_ZERO=self.GT_THAN_ZERO)

    def help_tree_summary(self):
        print 'Create tree summary of database contents, complete with \
indentation and info on the record.'

    def _set_numpy(self, val):
        np.set_printoptions(threshold=val)

    def _set_numpy_lw(self, val):
        np.set_printoptions(linewidth=val)

    def help_show_settings(self):
        print 'Show all settings and their current values.'

    def do_show_settings(self, line):
        table = Texttable()
        headers = ['Setting', 'Value']
        rows = [
            ['Numpy Line Width', self.NUMPY_LW],
            ['Numpy Threshold', self.NUMPY_THRESHOLD],
            ['Q Threshold', self.Q_THRESHOLD],
            ['Shape Threshold', self.SHAPE_THRESHOLD],
            ['Q Check', '>' if self.GT_THAN_ZERO else '<='],
            ['Show Menu Post Cmd?', 'Yes' if self.SHOW_MENU_AFTER_CMD else 'No'],
            ['Leaves Only Mode?', 'Yes' if self.VIEW_ONLY_LEAVES else 'No']
        ]
        rows.sort()
        rows.insert(0, headers)
        table.add_rows(rows)
        table.set_cols_align(['r', 'l'])
        table.set_deco(Texttable.HEADER | Texttable.VLINES)
        print table.draw()

    def help_save_all(self):
        print 'Save all nodes to text files. Default directory is \'results\'. \
Use toggle_leaves to toggle saving only the leaves of the tree. Use \
\'summarize\' after directory name to indicate whether or not a brief summary \
of the leafstrings should be written.'

    def do_save_all(self, line):
        if not File.select().count():
            print 'Database empty, nothing to save, returning.'
            return
        if not line:
            save_all(leaves_only=self.VIEW_ONLY_LEAVES)
            return
        line = line.split()
        summary = False
        directory = line[0]
        if not os.path.exists(directory):
            os.mkdir(directory)
        if len(line) > 1:
            if line[1].lower() == 'summarize':
                summary = True
        save_all(directory, leaves_only=self.VIEW_ONLY_LEAVES, summary=summary)

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
        print 'Set Numpy line width. Currently set to %i.' % self.NUMPY_LW

    def do_set_numpy_lw(self, line):
        if not line:
            print 'Numpy line width set to %i.' % self.NUMPY_LW
            return
        try:
            new_numpy_lw = int(line.strip())
            self._set_numpy_lw(new_numpy_lw)
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
        try:
            line = line.split()
            if not line:
                print 'Missing arguments.'
                return
            idx = int(line[0])
            view(idx)
        except ValueError:
            print '%s is not an integer.' % ' '.join(line)
            return

    def complete_view(self, text, line, begidx, endidx):
        if not text:
            completions = [i.id for i in File.select().where(File.processed == False).iterator()]
            return completions

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
                print 'Removing blank rows/cols.'
        master.loadtxt(target, blank=blank)

    def complete_convert_text(self, text, line, begidx, endidx):
        if not text:
            completions = [f for f in os.listdir('.')]
        else:
            completions = [f for f in os.listdir('.') if (f.startswith(text) and f.endswith('.txt'))]
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
        if not File.select().count():
            print 'No records in database, assuming first split.'
            initial = True
        master.split(target, initial=initial)

    def complete_load(self, text, line, begidx, endidx):
        if not text:
            completions = [f for f in os.listdir('.')]
        else:
            completions = [f for f in os.listdir('.') if (f.startswith(text) and f.endswith('.npz'))]
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
        if not File.select().count():
            print 'No records in database, canceling.'
            return
        partition_all(self.SHAPE_THRESHOLD, self.Q_THRESHOLD)

    def help_split(self):
        print 'Split record i, or a list of records using comma delimited list (ex: 1,3,4).'

    def do_split(self, line):
        if not File.select().count():
            print 'No records in database, canceling.'
            return
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
        if not File.select().count() and os.path.exists('files.db'):
            print 'Database empty, removing database to avoid clutter.'
            os.remove('files.db')
        else:
            print 'Database has records, will not be removing database.'
        print 'Goodbye.'
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
    Manager().cmdloop(intro=__intro__)
