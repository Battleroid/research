from peewee import CharField, SqliteDatabase, Model, PrimaryKeyField, BooleanField, DoubleField, \
    ForeignKeyField, TextField, IntegerField

database = SqliteDatabase('files.db')

class Base(Model):
    class Meta:
        database = database

class File(Base):
    id = PrimaryKeyField()
    parent = ForeignKeyField('self', null=True, related_name='children')
    filename = CharField(unique=True, null=False)
    ext = CharField(null=False)
    processed = BooleanField(default=False)
    a_elems = TextField(null=True, default='none')
    shape = IntegerField()
    q = DoubleField()
    leaf = BooleanField(default=False)

class Node(Base):
    id = PrimaryKeyField()
    root = BooleanField(default=False)  # is this necessary? can't we just select the items who have no parents?
    parent = ForeignKeyField('self', null=True, related_name='children')
    name = CharField(unique=True, null=False)
    shape = IntegerField()
    q = DoubleField()
    leaf = BooleanField(default=False)  # necessary as we want to record which are leaves according to File table
