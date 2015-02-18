from peewee import CharField, SqliteDatabase, Model, PrimaryKeyField, BooleanField, IntegerField, DoubleField

database = SqliteDatabase('files.db')

class Base(Model):
    class Meta:
        database = database

class File(Base):
    id = PrimaryKeyField()
    # parent_id = IntegerField(null=False) use self referential foreign key
    name = CharField(unique=True, null=False)
    processed = BooleanField(default=False)
    q = DoubleField()
