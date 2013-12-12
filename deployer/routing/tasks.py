from sqlalchemy.orm import sessionmaker, joinedload
from structlog import get_logger
from . import models
from deployer.applications.models import Instance
from deployer.utils import RecurrentTask


logger = get_logger()


class RoutesUpdater(RecurrentTask):
    """
    Once started, keeps the builds cache synchronized with the docker registry.
    """

    def __init__(self, app):
        self.frontend_name = app.config['FRONTEND_NAME']
        self.get_session = sessionmaker(bind=app.engine)

    def task(self):
        session = self.get_session()
        try:
            routes = session.query(models.Route).options(
                joinedload('instance')
            ).filter(models.Route.instance.has(Instance.stopped == None)).all()

            if routes:
                for route in routes:
                    route.update(self.frontend_name)
            else:
                logger.log('route.no_updates')
        finally:
            session.close()
