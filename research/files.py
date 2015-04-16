from peewee import CharField, SqliteDatabase, Model, PrimaryKeyField, BooleanField, DoubleField, \
    ForeignKeyField, TextField, IntegerField

database = SqliteDatabase('files.db')

class Base(Model):
    class Meta:
        database = database

class File(Base):
    """
    File model is used to keep track of grouping information as well as the binary tree order.
    """
    id = PrimaryKeyField()
    parent = ForeignKeyField('self', null=True, related_name='children')
    filename = CharField(unique=True, null=False)
    ext = CharField(null=False)
    processed = BooleanField(default=False)
    a_elems = TextField(null=True, default='none')
    shape = IntegerField()
    q = DoubleField()
    leaf = BooleanField(default=False)

class Item(Base):
    """
    Item model is used only to keep track of all files created during session. Used with :py:func:`manager.burn` to remove all files.
    """
    filename = CharField(unique=True, null=False)
