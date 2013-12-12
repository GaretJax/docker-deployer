from flask.ext.wtf import Form
from wtforms.ext.sqlalchemy.orm import model_form

from . import models


HostForm = model_form(
    models.Host, None, Form,
    exclude=[
    ],
    field_args={
    }
)
