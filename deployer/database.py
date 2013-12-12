from flask import abort

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, exc
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.types import TypeDecorator, TEXT
import json

from wtforms import fields as f
from wtforms.validators import StopValidation
from wtforms.ext.sqlalchemy import orm


_session_maker = None


def Session(*args, **kwargs):
    return _session_maker(*args, **kwargs)


def init_app(app):
    app.engine = create_engine(app.config['DATABASE'])
    global _session_maker
    _session_maker = scoped_session(sessionmaker(bind=app.engine))

    @app.teardown_request
    def shutdown_session(exc):
        if exc is None:
            _session_maker().commit()
        _session_maker.remove()
        return exc


def get_or_create(session, model, defaults={}, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        params = {k: v for k, v in kwargs.iteritems()
                  if not isinstance(v, ClauseElement)}
        params.update(defaults)
        instance = model(**params)
        session.add(instance)
        return instance, True


def get_or_abort(model, object_id, code=404):
    session = Session()
    result = session.query(model).get(object_id)
    if result is None:
        abort(code)
    return result


def get_one_or_abort(query, code=404):
    try:
        return query.one()
    except (exc.NoResultFound, exc.MultipleResultsFound):
        abort(code)


class JSON(TypeDecorator):
    """
    Represents an immutable structure as a json-encoded string.
    """

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class JSONField(f.TextAreaField):
    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        elif self.data is not None:
            return json.dumps(self.data, indent=4)
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = json.loads(valuelist[0])
            except ValueError:
                self.data = None


class JSONValidator(object):
    def __init__(self, message=None):
        if not message:
            message = u'Field content must be a valid JSON document.'
        self.message = message

    def __call__(self, form, field):
        data = field.raw_data[0].strip()
        if data:
            try:
                json.loads(data)
            except:
                raise StopValidation(self.message)


class ModelConverter(orm.ModelConverter):
    @orm.converts('JSON')
    def conv_JSON(self, field_args, **extra):
        self._string_common(field_args=field_args, **extra)
        field_args['validators'].insert(0, JSONValidator())
        return JSONField(**field_args)
