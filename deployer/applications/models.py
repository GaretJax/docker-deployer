import signal

from sqlalchemy import Column, Integer, String, Unicode, ForeignKey, Text
from sqlalchemy import DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.session import object_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import UniqueConstraint
from structlog import get_logger
from dateutil.parser import parse
from dateutil import tz
from datetime import datetime

from deployer import registry, database as db
from deployer.utils import get_container_ip
from deployer.hosts.models import Host


logger = get_logger()
Base = declarative_base()


class InstanceStateFilterMixin(object):
    @property
    def active_instances(self):
        return self.instances.filter(Instance.stopped == None)

    @property
    def inactive_instances(self):
        return self.instances.filter(Instance.stopped != None).order_by(
            Instance.stopped.desc())


class Application(InstanceStateFilterMixin, Base):
    __tablename__ = 'application'

    id = Column(Integer(), primary_key=True)
    key = Column(String(20), nullable=False, unique=True)
    name = Column(Unicode(120), nullable=False)
    description = Column(Text(), nullable=True)
    registry = Column(String(120), nullable=False)
    repository = Column(String(120), nullable=False)

    @property
    def full_repository(self):
        return '{}/{}'.format(self.registry, self.repository)

    def update_builds(self, session=None):
        log = logger.bind(
            app=self.key,
            registry=self.registry,
            repository=self.repository,
        )

        log.info('apps.update_started')

        remote_registry = registry.Registry(self.registry)
        tags = remote_registry.tags(self.repository)

        log.debug('apps.tags_fetched', count=len(tags))

        for tag, image in tags.iteritems():
            build = self.builds.filter(Build.tag == tag).first()
            needs_update = False
            if build:
                if build.image != image:
                    needs_update = True
                    log.info('apps.tag_changed', tag=tag,
                             old_image=build.image, new_image=image)
            else:
                build = Build(tag=tag)
                self.builds.append(build)
                needs_update = True
                log.info('apps.tag_added', image=image, tag=tag)

            if needs_update:
                spec = remote_registry.image_info(image)
                created = (parse(spec['created'])
                           .astimezone(tz.tzutc())
                           .replace(tzinfo=None))
                build.image = image
                build.created = created
                build.spec = spec

        log.info('apps.update_done')

    def get_instances(self, session):
        return (session.query(Instance)
                .join(Build)
                .filter(Build.application == self))

    @property
    def instances(self):
        return self.get_instances(object_session(self))


class Build(InstanceStateFilterMixin, Base):
    __tablename__ = 'build'

    id = Column(Integer(), primary_key=True)
    tag = Column(String(64), nullable=False)
    image = Column(String(64), nullable=False)
    created = Column(DateTime(), nullable=False)
    spec = Column(db.JSON(), nullable=False)
    application_id = Column(Integer(), ForeignKey('application.id'),
                            nullable=False)
    application = relationship(
        Application,
        backref=backref('builds', lazy='dynamic', order_by=created.desc())
    )

    __table_args__ = (
        UniqueConstraint('application_id', 'tag', name='build_id'),
    )

    @property
    def full_image(self):
        return '{}:{}'.format(self.application.full_repository, self.tag)

    def deploy(self, host, config):
        client = host.get_client()

        ports = {'{0[port]}/{0[type]}'.format(p): {} for p in config['ports']}
        volumes = {v: {} for v in config['shared-folders']}
        binds = {v: k for k, v in config['shared-folders'].iteritems()}

        port_bindings = (
            p for p in config['ports']
            if 'host_ip' in p or 'host_port' in p
        )
        port_bindings = {
            '{0[type]}/{0[port]}'.format(p): [{
                'HostIp': p.get('host_ip', ''),
                'HostPort': p.get('host_port', ''),
            }]
            for p in port_bindings
        }

        links = {v[1:]: k for k, v in config['links'].iteritems()}

        client.pull(
            self.application.full_repository,
            self.tag
        )

        container = client.create_container(
            self.full_image,
            command=['django-admin.py', 'runuwsgi'],
            #stdin_open=True, tty=True,
            ports=ports,
            volumes=volumes,
            environment=config['environment']
        )

        client.start(
            container,
            binds=binds,
            port_bindings=port_bindings,
            links=links
        )

        return Instance(
            started=datetime.now(),
            build=self,
            host=host,
            config=config,
            container=container['Id'],
        )


class DeploymentTemplate(Base):
    __tablename__ = 'deployment_template'

    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(120), nullable=False)
    description = Column(Text(), nullable=True)
    application_id = Column(
        Integer(),
        ForeignKey('application.id'),
        nullable=False
    )
    application = relationship(
        Application,
        backref=backref('templates', lazy='dynamic')
    )
    template = Column(db.JSON(), nullable=False)

    __table_args__ = (
        UniqueConstraint('application_id', 'name', name='template_id'),
    )


class Instance(Base):
    __tablename__ = 'instance'

    id = Column(Integer(), primary_key=True)
    started = Column(DateTime(), nullable=False)
    stopped = Column(DateTime(), nullable=True)

    build_id = Column(Integer(), ForeignKey('build.id'), nullable=False)
    build = relationship(
        Build,
        backref=backref('instances', lazy='dynamic', order_by=started.desc())
    )

    host_id = Column(Integer(), ForeignKey(Host.id), nullable=False)
    host = relationship(
        Host,
        backref=backref('instances', lazy='dynamic', order_by=started.desc())
    )

    config = Column(db.JSON(), nullable=False)
    container = Column(String(64), nullable=False)

    def get_logs(self):
        # TODO: Override version until
        # https://github.com/dotcloud/docker-py/pull/105
        # isn't merged and released.
        client = self.host.get_client(version='1.5')
        return client.logs(self.container)

    def get_ip(self):
        client = self.host.get_client()
        return get_container_ip(client, self.container)

    def stop(self):
        client = self.host.get_client()
        client.kill(self.container, signal=signal.SIGINT)
        client.wait(self.container)
        self.stopped = datetime.now()
