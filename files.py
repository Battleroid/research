from peewee import CharField, SqliteDatabase, Model, PrimaryKeyField, BooleanField, DoubleField, \
    ForeignKeyField

database = SqliteDatabase('files.db')


class Base(Model):
    class Meta:
        database = database


class File(Base):
    id = PrimaryKeyField()
    parent = ForeignKeyField('self', null=True, related_name='children')
    name = CharField(unique=True, null=False)
    ext = CharField(null=False)
    processed = BooleanField(default=False)
    q = DoubleField()
    g_one = BooleanField()
