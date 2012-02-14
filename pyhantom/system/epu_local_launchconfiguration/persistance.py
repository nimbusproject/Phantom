from sqlalchemy.orm import sessionmaker
from sqlalchemy import String, MetaData, Sequence
from sqlalchemy import Table
from sqlalchemy import Integer
from sqlalchemy import types
from sqlalchemy import Column
from datetime import datetime
from sqlalchemy.schema import ForeignKey, UniqueConstraint
from sqlalchemy.types import Boolean
from sqlalchemy.orm import mapper
from sqlalchemy.orm import relation
import sqlalchemy
import logging

metadata = MetaData()


launch_configuration_table = Table('launch_configuration', metadata,
    Column('column_id', Integer, Sequence('launch_configuration_id_seq'), primary_key=True),
    Column('user_name', String(1024), nullable=False),
    Column('ImageId', String(1024)),
    Column('InstanceType', String(1024)),
    Column('KernelId', String(1024)),
    Column('KeyName', String(1024)),
    Column('LaunchConfigurationARN', String(1024)),
    Column('LaunchConfigurationName', String(1024)),
    Column('RamdiskId', String(1024)),
    Column('UserData', String(1024)),
    Column('CreatedTime', types.TIMESTAMP(), default=datetime.now()),
    Column('InstanceMonitoring', Boolean, default=False),

    UniqueConstraint('user_name', 'LaunchConfigurationName', name='unique_lc_id')
    )

security_group_table = Table('security_group', metadata,
    Column('column_id', Integer, Sequence('security_group_id_seq'), primary_key=True),
    Column('lc_id', Integer, ForeignKey('launch_configuration.column_id')),
    Column('name', String(1024)),
    )

block_device_mappings_table = Table('block_device_mappings', metadata,
    Column('column_id', Integer, Sequence('security_group_id_seq'), primary_key=True),
    Column('lc_id', Integer, ForeignKey('launch_configuration.column_id')),
    Column('DeviceName', String(1024)),
    Column('VirtualName', String(1024)),
    Column('EBS_SnapshotId', String(1024)),
    Column('EBS_VolumeSize', Integer),
    )


class LaunchConfigurationObject(object):
    def __init__(self):
        pass

    def set_from_outtype(self, out_t, user_obj):
        self.user_name = user_obj.username
        self.ImageId = out_t.ImageId
        self.InstanceType = out_t.InstanceType
        self.KernelId = out_t.KernelId
        self.KeyName = out_t.KeyName
        self.LaunchConfigurationARN = out_t.LaunchConfigurationARN
        self.LaunchConfigurationName = out_t.LaunchConfigurationName
        self.RamdiskId = out_t.RamdiskId
        self.UserData = out_t.UserData
        self.CreatedTime = out_t.CreatedTime.date_time
        self.InstanceMonitoring = out_t.InstanceMonitoring.Enabled

        for sg in out_t.SecurityGroups.type_list:
            sgo = SecurityGroupObject()
            sgo.name = sg
            self.security_groups.append(sgo)

        # XXX todo: if we everuse EBS we will need that here.

class SecurityGroupObject(object):
    def __init__(self):
        pass

class BlockDeviceMappingsObject(object):
    def __init__(self):
        pass


mapper(BlockDeviceMappingsObject, block_device_mappings_table)
mapper(SecurityGroupObject, security_group_table)
mapper(LaunchConfigurationObject, launch_configuration_table, properties={
    'block_device_mappings': relation(BlockDeviceMappingsObject, backref="launch_configuration"),
    'security_groups':relation(SecurityGroupObject, backref="launch_configuration")})


class LaunchConfigurationDB(object):

    def __init__(self, dburl, module=None, logger=logging):

        if module is None:
            self._engine = sqlalchemy.create_engine(dburl, connect_args={'check_same_thread':False})
        else:
            self._engine = sqlalchemy.create_engine(dburl, module=module, connect_args={'check_same_thread':False})
        metadata.create_all(self._engine)
        self._SessionX = sessionmaker(bind=self._engine)
        self._Session = self._SessionX()
        self._log = logger

    def close(self):
        self._Session.close()

    def db_obj_add(self, obj):
        self._Session.add(obj)

    def db_commit(self):
        self._Session.commit()

    def delete_lc(self, obj):
        for sg in obj.security_groups:
            self._Session.delete(sg)
        self._Session.delete(obj)

    def get_lcs(self, user_object, names=None, max=-1, startToken=None, log=logging):

        q = self._Session.query(LaunchConfigurationObject)#.filter(LaunchConfigurationObject.user_name==user_object.username)

        if names:
            q = q.filter(LaunchConfigurationObject.LaunchConfigurationName.in_(names))
        if max > -1:
            q.limit(max)
        q = q.order_by(LaunchConfigurationObject.LaunchConfigurationName)
        if startToken:
            q = q.filter(LaunchConfigurationObject.LaunchConfigurationName >= startToken)

        return q.all()
