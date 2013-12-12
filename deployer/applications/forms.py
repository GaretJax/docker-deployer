from flask.ext.wtf import Form
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms import fields as f, validators

from deployer import database as db

from . import models
from deployer.hosts.models import Host


class ConfirmationForm(Form):
    pass


class HostnameValidator(validators.Regexp):
    def __init__(self, message=None):
        regex = r'^([a-z0-9][a-z0-9-]{0,62}\.)*[a-z0-9][a-z0-9-]{0,62}$'
        super(HostnameValidator, self).__init__(regex, message=message)


class DeploymentSetupForm(Form):
    host = QuerySelectField(u'Host', get_label=lambda h: h.name)
    template = QuerySelectField(u'Template', get_label=lambda t: t.name)
    hostname = f.StringField(u'Hostname', [validators.required(),
                                           validators.length(max=255),
                                           HostnameValidator()])

    def __init__(self, app, *args, **kwargs):
        super(DeploymentSetupForm, self).__init__(*args, **kwargs)
        self.app = app

        self.template.query_factory = self.get_templates_query
        self.host.query_factory = self.get_hosts_query

    def get_templates_query(self):
        return self.app.templates

    def get_hosts_query(self):
        return db.Session().query(Host)


ApplicationForm = model_form(
    models.Application, None, Form,
    exclude=[
        'builds',
        'templates',
    ],
    field_args={
        'key': {
            'description': (
                'An abbreviation for this application. This will be used in '
                'URLs and other places referencing the application.'
            ),
        },
        'registry': {
            'description': (
                'The URL of the remote Docker registry containing the images '
                'for this application.'
            )
        }
    }
)


TemplateForm = model_form(
    models.DeploymentTemplate, None, Form,
    converter=db.ModelConverter(),
    exclude=[
        'application',
    ],
    field_args={
        'template': {
            'description': 'A valid JSON deployment description.',
        },
    }
)
