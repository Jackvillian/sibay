from sqlalchemy import create_engine
db = create_engine('mysql+pymysql://air:airsibay@localhost/air', pool_recycle=3600)
from sqlalchemy import Table, Column, Integer, String, MetaData,DateTime
from sqlalchemy.sql import func
DB = MetaData()

users = Table(
   'users', DB,
   Column('id', Integer, primary_key = True),
   Column('userid', String(20)),
   Column('username', String(20)),
)
pointers = Table(
   'pointers', DB,
   Column('id', Integer, primary_key = True),
   Column('userid', String(20)),
   Column('tc',DateTime()),
)

DB.create_all(db)