import os
import re
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
    query = files.File.select()
    field_names = files.File._meta.get_field_names()
    items = [[f.id, f.processed, f.filename, f.q] for f in query]
    item_headers = [field_names[0], field_names[4], field_names[2], field_names[5]]
    col_width = [0, 1, 0, 0]
    for item in items:
        if len(str(item[0])) > col_width[0]:
            col_width[0] = len(str(item[0]))
        if len(item[2]) > col_width[2]:
            col_width[2] = len(item[2])
        if len(str(item[3])) > col_width[3]:
            col_width[3] = len(str(item[3]))
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
sf name -- split data stored in 'name', use only for first split
db c -- create tables for database manually
db d -- drop tables for database manually
db reset -- perform both 'db d' and 'db c'
burn -- removes all files associated with database
help -- print this information
exit -- exit the manager
    """


def partition(idx):
    try:
        idx = int(idx)
        parent = files.File.get(id=idx)
        if parent.processed:
            raise AlreadyProcessed
        print 'splitting %s' % parent.filename
        f1, f2 = master.split('.'.join((parent.filename, parent.ext)))
        parent.processed = True
        parent.save()
        files.File.create(parent=parent.id, filename=f1.filename, ext=f1.ext, q=f1.q)
        files.File.create(parent=parent.id, filename=f2.filename, ext=f2.ext, q=f2.q)
    except DoesNotExist:
        print 'ID %d does not exist!' % idx
    except AlreadyProcessed:
        print 'Cannot split %d, it has already been processed.' % idx
    except ZeroDivisionError:
        pass
    except master.CannotSplit:
        print 'Matrix cannot be split, shape is too small.'
        parent.processed = True
        parent.save()


def choice(choice):
    action = choice.split(' ')
    try:
        if action[0] == 's' and action[1]:
            partition(action[1])
        elif action[0] == 'sf' and action[1]:
            master.split(action[1], True)
        elif action[0] == 'db' and action[1] == 'c':
            create_table()
        elif action[0] == 'db' and action[1] == 'd':
            drop_tables()
        elif action[0] == 'db' and action[1] == 'reset':
            reset_database()
        elif action[0] == 'burn':
            burn()
        elif action[0] == 'q':
            sys.exit(0)
        elif action[0] == 'help':
            print_help()
        elif action[0] == 'exit':
            print 'exiting'
            sys.exit(0)
        else:
            print 'invalid input'
    except IndexError:
        print 'missing argument'
    except ValueError:
        print 'invalid input'


def menu():
    headers, items, width = build_choices()
    headline = ''
    for header in headers:
        headline += header.title() + ' '
    print headline
    separator = ''
    for length in width:
        portion = ''
        while len(portion) < length:
            portion += '-'
        separator += portion + ' '
    print separator
    for item in items:
        itemline = ''
        for part in item:
            itemline += part
        print itemline
    print ''


def burn():
    file_list = ['.'.join((i.filename, i.ext)) for i in files.File.select()]
    if not file_list:
        print 'database empty, skipping'
        return True
    for f in file_list:
        if os.path.exists(f):
            print 'removing %s' % f
            os.remove(f)
    print 'resetting database'
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


if __name__ == '__main__':
    check_database()
    main()
