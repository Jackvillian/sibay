from sqlalchemy import create_engine
engine = create_engine('mysql+pymysql://air:airsibay@localhost/air', pool_recycle=3600)
from sqlalchemy import Table, Column, Integer, String, MetaData,DateTime,Sequence,Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String(40))
    last_name = Column(String(40))
    username = Column(String(40))
    userid = Column(String(10))
    chattype = Column(String(10))

    def __init__(self,first_name,last_name, username, userid, chattype):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.userid = userid
        self.chattype = chattype

    def __repr__(self):
        return "<User('%s','%s', '%s', '%s', '%s')>" % (self.first_name,self.last_name ,self.username, self.userid, self.chattype)

class Locations(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    userid = Column(String(10))
    longitude = Column(String(10))
    latitude = Column(String(10))
    timestamp = (Column(String(60)))
    context_point = (Column(String(10)))


    def __init__(self,userid, longitude, latitude,timestamp, context_point):
        self.userid = userid
        self.longitude = longitude
        self.latitude = latitude
        self.timestamp = timestamp
        self.context_point = context_point
    def __repr__(self):
        return "<Locations('%s','%s', '%s', '%s', '%s')>" % ( self.userid, self.longitude, self.latitude, self.timestamp, self.context)

class Doc(Base):
    __tablename__ = 'doc'
    id = Column(Integer, primary_key=True)
    href = Column(String(200))
    name = Column(String(80))
    path = Column(String(80))
    timestamp = Column(String(40))
    archive = Column(Boolean, unique=False, server_default='1', nullable=False)


    def __init__(self,href,name,timestamp,path,archive):
        self.href = href
        self.name = name
        self.path = path
        self.timestamp = timestamp
        self.archive = archive


    def __repr__(self):
        return "<Doc('%s','%s', '%s', '%s','%s')>" % (self.href,self.name ,self.path, self.timestamp, self.archive)


#Base.create_all(engine)
Base.metadata.create_all(engine)