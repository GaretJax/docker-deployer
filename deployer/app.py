import os

from flask import Flask

from . import filters, context_processors, database, utils
from . import applications, views as _old, hosts

from .applications.tasks import BuildsUpdater
from .routing.tasks import RoutesUpdater


CONFIG_KEY_PREFIX = 'DEPLOYER_'


def create_app():
    app = Flask(__name__)

    for k, v in os.environ.iteritems():
        if k.startswith(CONFIG_KEY_PREFIX):
            app.config[k[len(CONFIG_KEY_PREFIX):]] = v

    if app.config['DEBUG']:
        from werkzeug.debug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
        app.debug = True

    app.url_map.converters['regex'] = utils.RegexConverter
    database.init_app(app)

    if 'NO_INIT_DB' not in app.config:
        from deployer.applications import models
        models.Base.metadata.create_all(app.engine)

        from deployer.hosts import models
        models.Base.metadata.create_all(app.engine)

        from deployer.routing import models
        models.Base.metadata.create_all(app.engine)

    app.register_blueprint(_old.views)
    app.register_blueprint(hosts.views, url_prefix='/hosts')
    app.register_blueprint(applications.views, url_prefix='/apps')

    app.context_processor(context_processors.register_functions)

    for name in filters.__all__:
        app.jinja_env.filters[name] = getattr(filters, name)

    BuildsUpdater(app).start(10, now=True)
    RoutesUpdater(app).start(10, now=True)

    return app


app = create_app()
