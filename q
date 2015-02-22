[1mdiff --git a/files.py b/files.py[m
[1mindex 7e0a207..c38b7a1 100644[m
[1m--- a/files.py[m
[1m+++ b/files.py[m
[36m@@ -1,14 +1,19 @@[m
[31m-from peewee import CharField, SqliteDatabase, Model, PrimaryKeyField, BooleanField, IntegerField, DoubleField[m
[32m+[m[32mfrom peewee import CharField, SqliteDatabase, Model, PrimaryKeyField, BooleanField, DoubleField, \[m
[32m+[m[32m    ForeignKeyField[m
 [m
 database = SqliteDatabase('files.db')[m
 [m
[32m+[m
 class Base(Model):[m
     class Meta:[m
         database = database[m
 [m
[32m+[m
 class File(Base):[m
     id = PrimaryKeyField()[m
[31m-    # parent_id = IntegerField(null=False) use self referential foreign key[m
[32m+[m[32m    parent = ForeignKeyField('self', null=True, related_name='children')[m
     name = CharField(unique=True, null=False)[m
[32m+[m[32m    ext = CharField(null=False)[m
     processed = BooleanField(default=False)[m
     q = DoubleField()[m
[32m+[m[32m    g_one = BooleanField()[m
