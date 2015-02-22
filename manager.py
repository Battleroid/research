import re
import sys
import master, files


def main():
    pass


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


def choice(choice):
    action = choice.split(' ')
    try:
        if action[0] == 's' and action[1]:
            print 'split', action[1]
        elif action[0] == 'db' and action[1] == 'c':
            print 'create db'
        elif action[0] == 'db' and action[1] == 'd':
            print 'delete db'
        elif action[0] == 'db' and action[1] == 'reset':
            print 'reset db'
        elif action[0] == 'q':
            print 'quit manager'
            sys.exit(0)
        else:
            print 'invalid input'
    except IndexError:
        print 'missing argument'
    except ValueError:
        print 'invalid input'


def menu():
    headers, items, width = build_choices()
    headline = ' '
    for header in headers:
        headline += header.title() + ' '
    print headline
    separator = ' '
    for length in width:
        portion = ''
        while len(portion) < length:
            portion += '-'
        separator += portion + ' '
    print separator
    for item in items:
        itemline = ' '
        for part in item:
            itemline += part
        print itemline


def create_table():
    files.database.connect()
    files.database.create_table(files.File)


def drop_tables():
    files.database.connect()
    files.database.drop_table(files.File)


def reset_database():
    create_table()
    drop_tables()


if __name__ == '__main__':
    main()