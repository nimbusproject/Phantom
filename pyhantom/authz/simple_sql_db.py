import logging
import sqlalchemy
from pyhantom.authz import PHAuthzIface, PhantomUserObject
from pyhantom.phantom_exceptions import PhantomAWSException, PhantomException
from sqlalchemy.orm import sessionmaker
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
    Column('displayname', String(512), nullable=False, unique=True),
    Column('access_key', String(512), nullable=False, unique=True),
    Column('access_secret', String(512), nullable=False),
    Column('CreatedTime', types.TIMESTAMP(), default=datetime.now()),
    )


class PhantomUserDBObject(object):
    def __init__(self):
        pass

mapper(PhantomUserDBObject, phantom_user_pass_table)

class SimpleSQL(PHAuthzIface):

    def __init__(self, cfg):
        self.cfg = cfg
        self._engine = sqlalchemy.create_engine(cfg.phantom.authz.dburl)
        metadata.create_all(self._engine)
        self._SessionX = sessionmaker(bind=self._engine)
        self._Session = self._SessionX()

    def _lookup_user(self, access_key):
        try:
            q = self._Session.query(PhantomUserDBObject)
            q = q.filter(PhantomUserDBObject.access_key==access_key)
            db_obj = q.first()
        except sqlalchemy.exc.SQLAlchemyError, ex:
            log(logging.ERROR, "A database error occurred while trying to access the user db %s" % (str(ex)))
            raise PhantomAWSException('InternalFailure')
        
        return db_obj

    def get_user_object_by_access_id(self, access_id):
        db_obj = self._lookup_user(access_id)
        if not db_obj:
            raise PhantomAWSException('InvalidClientTokenId')

        return PhantomUserObject(access_id, db_obj.access_secret)

    def get_user_object_by_display_name(self, display_name):
        try:
            q = self._Session.query(PhantomUserDBObject)
            q = q.filter(PhantomUserDBObject.display_name==display_name)
            db_obj = q.first()
            return PhantomUserObject(access_id, db_obj.access_secret)
        except sqlalchemy.exc.SQLAlchemyError, ex:
            log(logging.ERROR, "A database error occurred while trying to access the user db %s" % (str(ex)))
            raise PhantomAWSException('InternalFailure')

    def add_alter_user(self, displayname, access_key, access_secret):
        db_obj = self._lookup_user(access_key)
        if not db_obj:
            db_obj = PhantomUserDBObject()
            db_obj.access_key = access_key
        db_obj.access_secret = access_secret
        db_obj.displayname = displayname

        self._Session.add(db_obj)

    def remove_user(self, access_key):
        db_obj = self._lookup_user(access_key)
        if not db_obj:
            raise PhantomAWSException('InvalidClientTokenId')
        self._Session.delete(db_obj)

    def commit(self):
        self._Session.commit()

    def add_user(self, displayname, access_id, access_secret):
        self.add_alter_user(displayname, access_id, access_secret)
        self.commit()


    