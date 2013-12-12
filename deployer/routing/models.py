import socket
import struct

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from structlog import get_logger

from deployer.applications.models import Instance
from deployer.utils import get_container_ip


logger = get_logger()
Base = declarative_base()


class Route(Base):
    __tablename__ = 'route'

    id = Column(Integer(), primary_key=True)
    routing_key = Column(String(255), nullable=False)
    weight = Column(Integer(), nullable=False, default=1)
    instance_id = Column(Integer(), ForeignKey(Instance.id), nullable=False)
    instance = relationship(
        Instance,
        backref=backref('routes', lazy='dynamic')
    )

    def update(self, frontend_name):
        client = self.instance.host.get_client()
        instance_ip = self.instance.get_ip()
        router_ip = get_container_ip(client, frontend_name)

        payload = {
            'key': self.routing_key,
            'address': '{}:{}'.format(instance_ip, 5510),
        }

        msg = ''
        for k, v in payload.iteritems():
            k, v = str(k), str(v)
            msg += struct.pack('<h', len(k)) + str(k)
            msg += struct.pack('<h', len(v)) + v

        remove = self.instance.stopped is not None
        msg = struct.pack('<BhB', 224, len(msg), 1 if remove else 0) + msg
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(msg, (router_ip, 5500))

        logger.log(
            'route.discard' if remove else 'route.update',
            routing_key=self.routing_key,
            instance=instance_ip,
            host=self.instance.host.name,
            router=router_ip,
            weight=self.weight
        )
