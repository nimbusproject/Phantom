from datetime import datetime
import logging

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String, MetaData, Sequence
from sqlalchemy import Table
from sqlalchemy import types
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.pool import NullPool
import sqlalchemy

from pyhantom.authz import PHAuthzIface, PhantomUserObject
from pyhantom.phantom_exceptions import PhantomAWSException
from pyhantom.util import log

metadata = MetaData()

phantom_user_pass_table = Table('phantom_user_pass', metadata,
    Column('column_id', Integer, Sequence('launch_configuration_id_seq'), primary_key=True),
    Column('displayname', String(128), nullable=False, unique=True),
    Column('access_key', String(128), nullable=False, unique=True),
    Column('access_secret', String(128), nullable=False),
    Column('CreatedTime', types.TIMESTAMP(), default=datetime.now()),
    )


class PhantomUserDBObject(object):
    def __init__(self):
        pass

mapper(PhantomUserDBObject, phantom_user_pass_table)

def reset_db(func):
    def call(sqlobj, *args,**kwargs):
        sqlobj._open_dbobj()
        try:
            return func(sqlobj, *args, **kwargs)
        except sqlalchemy.exc.SQLAlchemyError, ex:
            log(logging.ERROR, "A database error occurred while trying to access the user db %s" % (str(ex)))
            raise PhantomAWSException('InternalFailure', ex)
        finally:
            sqlobj._close_dbobj()
    return call


class SimpleSQLSessionMaker(object):

    def __init__(self, dburl):
        self._engine = sqlalchemy.create_engine(dburl, poolclass=NullPool)
        metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine)

    def get_session(self):
        return self._Session()


class SimpleSQL(PHAuthzIface):

    def __init__(self, sessionmaker):
        self._sessionmaker = sessionmaker

    def _open_dbobj(self):
        self._session = self._sessionmaker.get_session()

    def _close_dbobj(self):
        if not self._session:
            return
        self._session.close()

    @reset_db
    def get_user_object_by_access_id(self, access_id):
        db_obj = self._lookup_user(access_id)
        if not db_obj:
            raise PhantomAWSException('InvalidClientTokenId')

        return PhantomUserObject(access_id, db_obj.access_secret, db_obj.displayname)

    @reset_db
    def get_user_object_by_display_name(self, display_name):
        try:
            q = self._session.query(PhantomUserDBObject)
            q = q.filter(PhantomUserDBObject.displayname==display_name)
            db_obj = q.first()
            if not db_obj:
                raise PhantomAWSException('InvalidClientTokenId')
            return PhantomUserObject(db_obj.access_key, db_obj.access_secret, db_obj.displayname)
        except sqlalchemy.exc.SQLAlchemyError, ex:
            log(logging.ERROR, "A database error occurred while trying to access the user db %s" % (str(ex)))
            raise PhantomAWSException('InternalFailure')

    def _add_alter_user(self, displayname, access_key, access_secret):
        db_obj = self._lookup_user(access_key)
        if not db_obj:
            db_obj = PhantomUserDBObject()
            db_obj.access_key = access_key
        db_obj.access_secret = access_secret
        db_obj.displayname = displayname
        self._session.add(db_obj)

    @reset_db
    def remove_user(self, access_key):
        db_obj = self._lookup_user(access_key)
        if not db_obj:
            raise PhantomAWSException('InvalidClientTokenId')
        self._session.delete(db_obj)
        return True

    @reset_db
    def add_user(self, displayname, access_id, access_secret):
        self._add_alter_user(displayname, access_id, access_secret)
        self.commit()

    def _lookup_user(self, access_key):
        q = self._session.query(PhantomUserDBObject)
        q = q.filter(PhantomUserDBObject.access_key==access_key)
        db_obj = q.first()
        return db_obj

    def commit(self):
        self._session.commit()

    def close(self):
        self._session.close()
