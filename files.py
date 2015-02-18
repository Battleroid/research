from peewee import CharField, SqliteDatabase, Model, PrimaryKeyField, BooleanField, IntegerField

database = SqliteDatabase('files.db')

class Base(Model):
    class Meta:
        database = database

class File(Base):
    id = PrimaryKeyField()
    parent_id = IntegerField(null=False)
    name = CharField(unique=True, null=False)
    processed = BooleanField(default=False)
