from sqlalchemy import create_engine
engine = create_engine('mysql+pymysql://air:airsibay@localhost/air', pool_recycle=3600)
from sqlalchemy import Table, Column, Integer, String, MetaData,DateTime,Sequence
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(10))
    userid = Column(String(10))
    chatid = Column(String(10))

    def __init__(self, username, userid, chatid):
        self.name = username
        self.userid = userid
        self.chatid = chatid

    def __repr__(self):
        return "<User('%s','%s', '%s')>" % (self.username, self.userid, self.chatid)

class locations(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    username = Column(String(10))
    longitude = Column(String(10))
    latitude = Column(String(10))

    def __init__(self, username, longitude, latitude):
        self.name = username
        self.userid = longitude
        self.chatid = latitude

    def __repr__(self):
        return "<User('%s','%s', '%s')>" % (self.username, self.longitude, self.latitude)

#Base.create_all(engine)
Base.metadata.create_all(engine)