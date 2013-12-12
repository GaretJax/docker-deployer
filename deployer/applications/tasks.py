from sqlalchemy.orm import sessionmaker

from . import models
from deployer.utils import RecurrentTask


class BuildsUpdater(RecurrentTask):
    """
    Once started, keeps the builds cache synchronized with the docker registry.
    """

    def __init__(self, app):
        self.get_session = sessionmaker(bind=app.engine)

    def task(self):
        session = self.get_session()
        try:
            try:
                for app in session.query(models.Application).all():
                    app.update_builds()
            except:
                session.rollback()
                raise
            else:
                session.commit()
        finally:
            session.close()
