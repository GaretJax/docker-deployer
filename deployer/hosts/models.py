from sqlalchemy import Column, Integer, String, Unicode, Enum
from sqlalchemy.ext.declarative import declarative_base

import docker


Base = declarative_base()


class Host(Base):
    __tablename__ = 'host'

    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(120), nullable=False, unique=True)
    url = Column(String(120), nullable=False)
    version = Column(Enum('1.6', '1.7'), nullable=False)

    @property
    def active_instances(self):
        Instance = self.instances._entities[0].type
        return self.instances.filter(Instance.stopped == None)

    @property
    def inactive_instances(self):
        Instance = self.instances._entities[0].type
        return self.instances.filter(Instance.stopped != None)

    def get_client(self, version=None):
        if version is None:
            version = self.version
        return docker.Client(base_url=self.url, version=version)
