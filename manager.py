import numpy as np
import os
import sys
from peewee import DoesNotExist
import master
import files

class AlreadyProcessed(Exception):
    def __init__(self, message=None):
        if not message:
            self.message = 'Matrix already processed, cannot reprocess.'
        self.message = message

def main():
    while True:
        menu()
        c = raw_input('> ')
        choice(c)

def build_choices():
    global VIEW_ONLY_LEAVES
    if VIEW_ONLY_LEAVES:
        query = files.File.select().where(files.File.leaf == True).iterator()
    else:
        query = files.File.select().iterator()
    field_names = files.File._meta.get_field_names()
    items = [[f.id, f.processed, f.filename, f.q, f.shape] for f in query]
    # id, processed, filename, q, shape, a_elems
    item_headers = [field_names[0], field_names[4], field_names[2], field_names[7], field_names[6]]
    col_width = [0, 1, 0, 0, 0]
    for item in items:
        if len(str(item[0])) > col_width[0]:
            col_width[0] = len(str(item[0]))
        if len(str(item[1])) > col_width[1]:
            col_width[1] = len(str(item[1]))
        if len(item[2]) > col_width[2]:
            col_width[2] = len(item[2])
        if len(str(item[3])) > col_width[3]:
            col_width[3] = len(str(item[3]))
        if len(str(item[4])) > col_width[4]:
            col_width[4] = len(str(item[4]))
    for i, header in enumerate(item_headers):
        if len(header) > col_width[i]:
            col_width[i] = len(header)
    menu_items = []
    for item in items:
        foo = []
        for i, part in enumerate(item):
            foo.append(str(part).ljust(col_width[i] + 1))
        menu_items.append(foo)
    return item_headers, menu_items, col_width

def print_help():
    print """
s i -- split matrix i
sr i-j -- split nodes i through j
ss i,j,k -- split a list of nodes with a comma delimiter
sall -- recursively partition until all values are false
v i -- view matrix information of i, if it has a parent it is viewable as well
tl -- toggle leaves only mode
sf name -- split data stored in 'name', use only for first split
lt name -- load text file and split
db c -- create tables for database manually
db d -- drop tables for database manually
db reset -- perform both 'db d' and 'db c'
burn -- removes all files associated with database
npt -- unlock numpy threshold
shape -- change shape threshold (default 5)
qth -- change q threshold (default 0)
help -- print this information
exit -- exit the manager
    """

def partition(idx):
    global SHAPE_THRESHOLD
    global Q_THRESHOLD
    try:
        idx = int(idx)
        parent = files.File.get(id=idx)
        if parent.processed:
            raise AlreadyProcessed
        if SHAPE_THRESHOLD >= parent.shape:
            raise master.CannotSplit(message='Matrix cannot be split, exceeds threshold of %dx%d.' % (SHAPE_THRESHOLD, SHAPE_THRESHOLD))
        # check q of parent before moving on?
        # if Q_THRESHOLD >= parent.q:
        #     raise master.CannotSplit(message='Matrix cannot be split, exceeds Q threshold of %d.' % Q_THRESHOLD)
        print 'Splitting %s' % parent.filename
        # make note: you may end up with MORE files than are visible in the database, this is
        # because the split function SAVES the files regardless before returning the results as
        # Part objects. So the database is still correct, you just might end up with more cleanup than
        # you think.
        f1, f2 = master.split('.'.join((parent.filename, parent.ext)))
        # question: if the Q threshold is on either do we save them? Or do we not save that node?
        # if we only abandon the one, just make it to an if statement for each
        if f1.q <= Q_THRESHOLD or f2.q <= Q_THRESHOLD:
            raise master.CannotSplit(message='Matrix cannot be split, exceeds Q threshold of %d.' % Q_THRESHOLD)
        files.File.create(parent=parent.id, filename=f1.filename, ext=f1.ext, q=f1.q, shape=f1.shape, a_elems=f1.a_elems)
        files.File.create(parent=parent.id, filename=f2.filename, ext=f2.ext, q=f2.q, shape=f2.shape, a_elems=f2.a_elems)
    except DoesNotExist:
        print 'ID %d does not exist!' % idx
    except AlreadyProcessed:
        print 'Cannot split %d, it has already been processed.' % idx
    except ZeroDivisionError:
        pass
    except master.CannotSplit, e:
        # sets parent leaf to true, however, may need to change
        parent.leaf = True
        print e.message
    finally:
        parent.processed = True
        parent.save()

def partitionall():
    if [x.processed for x in files.File.select().where(files.File.processed == False).iterator()]:
        [partition(z.id) for z in files.File.select().where(files.File.processed == False).iterator()]
    if [x.processed for x in files.File.select().where(files.File.processed == False).iterator()]:
        return partitionall()
    else:
        print 'Finished'
        return

def view(idx):
    try:
        idx = int(idx)
        target = files.File.get(id=idx)
        data = np.load(target.filename + '.' + target.ext)
        print 'Matrix', target.filename, os.linesep, data['a'] 
        print 'Origin elements for', target.filename,  os.linesep, data['a_elems'] 
        parent_id = target.parent.id
        if confirm('Do you want to view the parent? y/n: '):
            view(parent_id)
    except DoesNotExist:
        print 'ID %d does not exist!' % idx
    except AttributeError:
        print 'No parent could be found (possible that this is the master split).'

def confirm(message='Are you sure? y/n: '):
    while True:
        i = raw_input(message)
        if i[0] == 'y':
            return True
        elif i[0] == 'n':
            return False
        else:
            print 'Invalid input'

def choice(choice):
    action = choice.split(' ')
    try:
        if action[0] == 's' and action[1]:
            partition(action[1])
        elif action[0] == 'sr' and action[1]:
            begin, end = action[1].split('-')[:2]
            if end > begin:
                for i in range(int(begin), int(end) + 1):
                    partition(i)
            else:
                print 'Beginning of range must be lower than ending'
        elif action[0] == 'ss' and action[1]:
            to_part = action[1].split(',')
            [int(x) for x in to_part]
            for piece in to_part:
                partition(piece)
        elif action[0] == 'sall':
            partitionall()
        elif action[0] == 'v' and action[1]:
            view(action[1])
        elif action[0] == 'tl':
            global VIEW_ONLY_LEAVES
            VIEW_ONLY_LEAVES = not VIEW_ONLY_LEAVES
            print 'Toggled Leaves Only mode to %s' % str(VIEW_ONLY_LEAVES)
        elif action[0] == 'sf' and action[1]:
            master.split(action[1], True)
        elif action[0] == 'lt':
            master.loadtxt(action[1])
        elif action[0] == 'db' and action[1] == 'c':
            create_table()
        elif action[0] == 'db' and action[1] == 'd':
            drop_tables()
        elif action[0] == 'db' and action[1] == 'reset':
            if confirm():
                reset_database()
            else:
                print 'Aborted'
        elif action[0] == 'burn':
            if confirm():
                burn()
            else:
                print 'Aborted'
        elif action[0] == 'npt':
            np.set_printoptions(threshold=np.nan)
            print 'Unlocked numpy threshold'
        elif action[0] == 'shape':
            global SHAPE_THRESHOLD
            SHAPE_THRESHOLD = int(action[1])
            print 'Shape threshold changed to %d' % SHAPE_THRESHOLD
        elif action[0] == 'qth':
            global Q_THRESHOLD
            Q_THRESHOLD = float(action[1])
            print 'Q threshold changed to %d' % Q_THRESHOLD
        elif action[0] == 'q':
            sys.exit(0)
        elif action[0] == 'help':
            print_help()
        elif action[0] == 'exit':
            print 'Exiting'
            sys.exit(0)
        else:
            print 'Invalid input'
    except IndexError:
        print 'Missing argument'
    except (ValueError, TypeError, UnboundLocalError):
        print 'Invalid input'
    except IOError:
        print 'File cannot be found.'

def menu():
    # headers
    headers, items, width = build_choices()
    headline = ''
    for idx, header in enumerate(headers):
        headline += header.title().ljust(width[idx]) + ' '
    print headline
    # ---
    separator = ''
    for length in width:
        portion = ''
        while len(portion) < length:
            portion += '-'
        separator += portion + ' '
    print separator
    # items
    for item in items:
        itemline = ''
        for part in item:
            itemline += part
        print itemline
    print ''

def burn():
    file_list = ['.'.join((i.filename, i.ext)) for i in files.File.select()]
    if not file_list:
        print 'Database empty, skipping.'
        return True
    for f in file_list:
        if os.path.exists(f):
            print 'Removing %s' % f
            os.remove(f)
    print 'Resetting database'
    reset_database()

def create_table():
    files.database.connect()
    files.database.create_table(files.File)

def drop_tables():
    files.database.connect()
    files.database.drop_table(files.File)

def reset_database():
    drop_tables()
    create_table()

def check_database():
    if not files.File.table_exists():
        create_table()

SHAPE_THRESHOLD = 5
Q_THRESHOLD = 0
VIEW_ONLY_LEAVES = False

if __name__ == '__main__':
    check_database()
    main()
