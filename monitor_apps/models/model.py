import configparser
import os.path
from datetime import datetime
config = configparser.ConfigParser()
config_path=os.path.join(os.path.dirname(__file__), '../config.ini')
config.read(config_path)
from sqlalchemy import create_engine
mydb='mysql+pymysql://'+config.get('mysql','user')+':'+config.get('mysql','password')+'@'+config.get('mysql','host')+'/'+config.get('mysql','db')
#print(mydb)
engine = create_engine(mydb, pool_recycle=3600)
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
        return '{} {} {} {} {}'.format(self.first_name,self.last_name ,self.username, self.userid, self.chattype)

class Log(Base):
    __tablename__ = 'log'
    id = Column(Integer, primary_key=True)
    userid = Column(String(40))
    step = Column(String(40))
    timestamp_utc = Column(DateTime, default=datetime.utcnow)


    def __init__(self,userid,step,timestamp_utc):
        self.userid = userid
        self.step = step
        self.timestamp_utc = timestamp_utc

    def __repr__(self):
        return '{} {} {}'.format(self.userid,self.step ,self.timestamp_utc)


class Blacklist(Base):
    __tablename__ = 'blacklist'
    id = Column(Integer, primary_key=True)
    userid = Column(String(40))
    reason = Column(String(120))

    def __init__(self, userid, reason):
        self.userid = userid
        self.reason = reason

    def __repr__(self):
        return '{} {}'.format(self.userid, self.reason)

class Sensor(Base):
    __tablename__ = 'sensors'
    id = Column(Integer, primary_key=True)
    name = Column(String(40))
    uid = Column(String(40))
    type = Column(String(40))
    address = Column(String(10))
    value = Column(String(10))
    timestamp_utc=Column(DateTime, default=datetime.utcnow)

    def __init__(self, name, uid, type, address, value,timestamp_utc):
        self.name = name
        self.uid = uid
        self.type = type
        self.address = address
        self.value = value
        self.timestamp_utc = timestamp_utc

    def __repr__(self):
        return '{} {} {} {} {} {}'.format(self.name, self.uid, self.type, self.address, self.value, self.timestamp_utc)

class Locations(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    userid = Column(String(10))
    longitude = Column(String(10))
    latitude = Column(String(10))
    timestamp = (Column(String(60)))
    context = (Column(String(10)))
    archive = Column(Boolean, unique=False, server_default='1', nullable=False)


    def __init__(self,userid, longitude, latitude,timestamp, context,archive):
        self.userid = userid
        self.longitude = longitude
        self.latitude = latitude
        self.timestamp = timestamp
        self.context = context
        self.archive = archive
    def __repr__(self):
        return '{} {} {} {} {} {}'.format( self.userid, self.longitude, self.latitude, self.timestamp, self.context, self.archive)

class Maps(Base):
    __tablename__ = 'maps'
    id = Column(Integer, primary_key=True)
    path = Column(String(80))
    timestamp = (Column(String(60)))
    archive = Column(Boolean, unique=False, server_default='1', nullable=False)
    publish = Column(Boolean, unique=False, server_default='1', nullable=False)
    def __init__(self,path,timestamp,archive,publish):
        self.path = path
        self.timestamp = timestamp
        self.archive = archive
        self.publish = publish
    def __repr__(self):
        return '{} {} {} {}'.format( self.path, self.timestamp, self.archive, self.publish)


class Doc(Base):
    __tablename__ = 'doc'
    id = Column(Integer, primary_key=True)
    href = Column(String(200))
    name = Column(String(80))
    path = Column(String(80))
    timestamp = Column(String(40))
    archive = Column(Boolean, unique=False, server_default='1', nullable=False)
    publish = Column(Boolean, unique=False, server_default='1', nullable=False)

    def __init__(self,href,name,timestamp,path,archive,publish):
        self.href = href
        self.name = name
        self.path = path
        self.timestamp = timestamp
        self.archive = archive
        self.publish = publish


    def __repr__(self):
        return '{} {} {} {} {} {}'.format(self.href,self.name ,self.path, self.timestamp, self.archive, self.publish)


#Base.create_all(engine)
Base.metadata.create_all(engine)