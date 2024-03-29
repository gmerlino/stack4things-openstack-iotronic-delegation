# -*- encoding: utf-8 -*-
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
SQLAlchemy models for iot data.
"""

import json

from oslo_config import cfg
from oslo_db.sqlalchemy import models
import six.moves.urllib.parse as urlparse
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import schema
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator, TEXT
from iotronic.common import paths

sql_opts = [
    cfg.StrOpt('mysql_engine',
               default='InnoDB',
               help='MySQL engine to use.')
]

_DEFAULT_SQL_CONNECTION = 'sqlite:///' + \
                          paths.state_path_def('iotronic.sqlite')

cfg.CONF.register_opts(sql_opts, 'database')


def table_args():
    engine_name = urlparse.urlparse(cfg.CONF.database.connection).scheme
    if engine_name == 'mysql':
        return {'mysql_engine': cfg.CONF.database.mysql_engine,
                'mysql_charset': "utf8"}
    return None


class JsonEncodedType(TypeDecorator):
    """Abstract base type serialized as json-encoded string in db."""
    type = None
    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            # Save default value according to current type to keep the
            # interface the consistent.
            value = self.type()
        elif not isinstance(value, self.type):
            raise TypeError("%s supposes to store %s objects, but %s given"
                            % (self.__class__.__name__,
                               self.type.__name__,
                               type(value).__name__))
        serialized_value = json.dumps(value)
        return serialized_value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class JSONEncodedDict(JsonEncodedType):
    """Represents dict serialized as json-encoded string in db."""
    type = dict


class JSONEncodedList(JsonEncodedType):
    """Represents list serialized as json-encoded string in db."""
    type = list


class IotronicBase(models.TimestampMixin,
                   models.ModelBase):
    metadata = None

    def as_dict(self):
        d = {}
        for c in self.__table__.columns:
            d[c.name] = self[c.name]
        return d

    def save(self, session=None):
        import iotronic.db.sqlalchemy.api as db_api

        if session is None:
            session = db_api.get_session()

        super(IotronicBase, self).save(session)


Base = declarative_base(cls=IotronicBase)


class Conductor(Base):
    """Represents a conductor service entry."""

    __tablename__ = 'conductors'
    __table_args__ = (
        schema.UniqueConstraint('hostname', name='uniq_conductors0hostname'),
        table_args()
    )
    id = Column(Integer, primary_key=True)
    hostname = Column(String(255), nullable=False)
    online = Column(Boolean, default=True)


class WampAgent(Base):
    """Represents a wampagent service entry."""

    __tablename__ = 'wampagents'
    __table_args__ = (
        schema.UniqueConstraint('hostname', name='uniq_wampagentss0hostname'),
        table_args()
    )
    id = Column(Integer, primary_key=True)
    hostname = Column(String(255), nullable=False)
    wsurl = Column(String(255), nullable=False)
    online = Column(Boolean, default=True)
    ragent = Column(Boolean, default=False)


class Board(Base):
    """Represents a Board."""

    __tablename__ = 'boards'

    __table_args__ = (
        schema.UniqueConstraint('uuid', name='uniq_boards0uuid'),
        schema.UniqueConstraint('code', name='uniq_boards0code'),
        table_args())
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36))
    code = Column(String(25))
    status = Column(String(15), nullable=True)
    name = Column(String(255), nullable=True)
    type = Column(String(255))
    agent = Column(String(255), nullable=True)
    owner = Column(String(36))
    project = Column(String(36))
    fleet = Column(String(36), ForeignKey('fleets.uuid'), nullable=True)
    lr_version = Column(String(20), nullable=True)
    connectivity = Column(JSONEncodedDict)
    mobile = Column(Boolean, default=False)
    config = Column(JSONEncodedDict)
    extra = Column(JSONEncodedDict)


class Delegation(Base):
    """Represents a Delegation instance."""
    __tablename__ = 'delegations'

    __table_args__ = (
        schema.UniqueConstraint('uuid', name='uniq_delegations0uuid'),
        schema.UniqueConstraint('delegated', 'node',
                                name='uniq_delegations0delegated_node'),
        table_args())
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), ForeignKey('boards.id'))
    delegated = Column(String(32), ForeignKey('users.uuid'))
    delegator = Column(String(32), ForeignKey('users.uuid'))
    parent = Column(String(36), ForeignKey(
        'delegations.uuid', ondelete='CASCADE'))
    role = Column(String(255), ForeignKey('roles.name'))
    node = Column(String(36), nullable=True)
    type = Column(String(255), nullable=True)


class Nodetype(Base):
    """Represents a Node_Type instance."""
    __tablename__ = 'node_types'

    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_node_types0name'),
        table_args())
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)


class Role(Base):
    """Represents a Role instance."""
    __tablename__ = 'roles'

    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_roles0name'),
        table_args())
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    permissions = Column(JSONEncodedList, nullable=True)
    description = Column(String(255), nullable=True)


class Operation(Base):
    """Represents a Operation instance."""
    __tablename__ = 'operations'

    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_operations0name'),
        table_args())
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=True)


class User(Base):
    """Represents a User instance."""
    __tablename__ = 'users'

    __table_args__ = (
        schema.UniqueConstraint('name', name='uniq_users0name'),
        schema.UniqueConstraint('uuid', name='uniq_users0uuid'),
        table_args())
    id = Column(Integer, primary_key=True)
    uuid = Column(String(32), nullable=False)
    name = Column(String(255), nullable=True)
    base_role = Column(String(255), ForeignKey('roles.name'))


class Location(Base):
    """Represents a location of a board."""

    __tablename__ = 'locations'
    __table_args__ = (
        table_args())
    id = Column(Integer, primary_key=True)
    longitude = Column(String(18), nullable=True)
    latitude = Column(String(18), nullable=True)
    altitude = Column(String(18), nullable=True)
    board_id = Column(Integer, ForeignKey('boards.id'))


class SessionWP(Base):
    """Represents a session of a board."""

    __tablename__ = 'sessions'
    __table_args__ = (
        schema.UniqueConstraint(
            'session_id', 'board_uuid',
            name='uniq_board_session_id0session_id'),
        table_args())
    id = Column(Integer, primary_key=True)
    valid = Column(Boolean, default=True)
    session_id = Column(String(20))
    board_uuid = Column(String(36))
    board_id = Column(Integer, ForeignKey('boards.id'))


class Plugin(Base):
    """Represents a plugin."""

    __tablename__ = 'plugins'
    __table_args__ = (
        schema.UniqueConstraint('uuid', name='uniq_plugins0uuid'),
        table_args())
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36))
    name = Column(String(36))
    owner = Column(String(36))
    public = Column(Boolean, default=False)
    code = Column(TEXT)
    callable = Column(Boolean)
    parameters = Column(JSONEncodedDict)
    extra = Column(JSONEncodedDict)


class InjectionPlugin(Base):
    """Represents an plugin injection on board."""

    __tablename__ = 'injection_plugins'
    __table_args__ = (
        table_args())
    id = Column(Integer, primary_key=True)
    board_uuid = Column(String(36), ForeignKey('boards.uuid'))
    plugin_uuid = Column(String(36), ForeignKey('plugins.uuid'))
    onboot = Column(Boolean, default=False)
    status = Column(String(15))


class Service(Base):
    """Represents a service."""

    __tablename__ = 'services'
    __table_args__ = (
        schema.UniqueConstraint('uuid', name='uniq_services0uuid'),
        table_args())
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36))
    name = Column(String(36))
    project = Column(String(36))
    port = Column(Integer)
    protocol = Column(String(3))
    extra = Column(JSONEncodedDict)


class ExposedService(Base):
    """Represents an exposed service on board."""

    __tablename__ = 'exposed_services'
    __table_args__ = (
        table_args())
    id = Column(Integer, primary_key=True)
    board_uuid = Column(String(36), ForeignKey('boards.uuid'))
    service_uuid = Column(String(36), ForeignKey('services.uuid'))
    public_port = Column(Integer)


class Port(Base):
    """Represents a port on board."""

    __tablename__ = 'ports_on_boards'
    #    __table_args__ = (
    #        schema.UniqueConstraint('port_uuid', name='uniq_ports0uuid'),
    #        table_args()
    #    )
    id = Column(Integer, primary_key=True)
    board_uuid = Column(String(40), ForeignKey('boards.uuid'))
    uuid = Column(String(40))
    VIF_name = Column(String(30))
    #    project = Column(String(36))
    MAC_add = Column(String(32))
    ip = Column(String(36))
    #    status = Column(String(36))
    network = Column(String(36))


#    security_groups = Column(String(40))

class Fleet(Base):
    """Represents a fleet."""

    __tablename__ = 'fleets'
    __table_args__ = (
        schema.UniqueConstraint('uuid', name='uniq_fleets0uuid'),
        table_args())
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36))
    name = Column(String(36))
    project = Column(String(36))
    description = Column(String(300))
    extra = Column(JSONEncodedDict)


class Webservice(Base):
    """Represents a webservices."""

    __tablename__ = 'webservices'
    __table_args__ = (
        schema.UniqueConstraint('uuid', name='uniq_webservices0uuid'),
        schema.UniqueConstraint('board_uuid', 'port', 'name',
                                name='uniq_webservices_on_board'),
        schema.UniqueConstraint('port', 'board_uuid',
                                name='uniq_webservices_port_and_board'),
        table_args())
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36))
    port = Column(Integer)
    name = Column(String(45))
    board_uuid = Column(String(36), ForeignKey('boards.uuid'), nullable=True)
    secure = Column(Boolean, default=True)
    extra = Column(JSONEncodedDict)


class EnabledWebservice(Base):
    """The boards in which webservices are enabled."""

    __tablename__ = 'enabled_webservices'
    id = Column(Integer, primary_key=True)
    board_uuid = Column(String(36), ForeignKey('boards.uuid'), nullable=True)
    http_port = Column(Integer)
    https_port = Column(Integer)
    dns = Column(String(100))
    zone = Column(String(100))
    extra = Column(JSONEncodedDict)
