import logging
import sqlalchemy
from pyhantom.authz import PHAuthzIface, PhantomUserObject
from pyhantom.phantom_exceptions import PhantomAWSException, PhantomException
from phantomsql import PhantomSQL
from sqlalchemy import String, MetaData, Sequence
from sqlalchemy import Table
from sqlalchemy import Integer
from sqlalchemy import types
from sqlalchemy import Column
from datetime import datetime
from sqlalchemy.orm import mapper
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


class SimpleSQL(PHAuthzIface):

    def __init__(self, dburl):
        self._dburl = dburl
        # open and close to discover obvious errors early
        self._open_dbobj()
        self._close_dbobj()

    def _open_dbobj(self):
        self._phantom_sql = PhantomSQL(self._dburl)

    def _close_dbobj(self):
        if not self._phantom_sql:
            return  
        self._phantom_sql.close()

    @reset_db
    def get_user_object_by_access_id(self, access_id):
        db_obj = self._phantom_sql.get_user_object_by_access_id(access_id)
        if not db_obj:
            raise PhantomAWSException('InvalidClientTokenId')

        return PhantomUserObject(access_id, db_obj.access_secret, db_obj.displayname)

    @reset_db
    def get_user_object_by_display_name(self, display_name):
        try:
            db_obj = self._phantom_sql.get_user_object_by_display_name(display_name)
            if not db_obj:
                raise PhantomAWSException('InvalidClientTokenId')
            return PhantomUserObject(db_obj.access_key, db_obj.access_secret, db_obj.displayname)
        except sqlalchemy.exc.SQLAlchemyError, ex:
            log(logging.ERROR, "A database error occurred while trying to access the user db %s" % (str(ex)))
            raise PhantomAWSException('InternalFailure')

    @reset_db
    def add_alter_user(self, displayname, access_key, access_secret):
        self._phantom_sql.add_alter_user(displayname, access_key, access_secret)

    @reset_db
    def remove_user(self, access_key):
        removed = self._phantom_sql.remove_user(access_key)
        if not removed:
            raise PhantomAWSException('InvalidClientTokenId')

    def commit(self):
        self._phantom_sql.commit()

    def close(self):
        self._phantom_sql.close()

    @reset_db
    def add_user(self, displayname, access_id, access_secret):
        self._phantom_sql.add_user(displayname, access_id, access_secret)


    