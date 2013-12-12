from flask import Blueprint, render_template, redirect, url_for, current_app

from deployer import database as db
from deployer.routing.models import Route
from deployer.utils import xhr_form, allow_traffic, get_container_ip
from . import models, forms


views = Blueprint('apps', __name__, template_folder='templates')


def get_app(key):
    query = db.Session().query(models.Application).filter_by(key=key)
    return db.get_one_or_abort(query)


@views.route('/')
def index():
    apps = db.Session().query(models.Application).all()
    return render_template('applications.html', apps=apps)


@views.route('/<regex("[A-Z0-9]+"):app_key>/')
def app(app_key):
    return render_template('application.html', app=get_app(app_key))


@views.route('/new/', methods=['GET', 'POST'], endpoint='new')
@views.route('/<regex("[A-Z0-9]+"):app_key>/edit/', methods=['GET', 'POST'])
@xhr_form
def edit(app_key=None):
    create = app_key is None
    app = None if create else get_app(app_key)
    form = forms.ApplicationForm(obj=app)

    if form.validate_on_submit():
        session = db.Session()
        if create:
            app = models.Application()
        form.populate_obj(app)
        session.add(app)
        session.commit()
        return redirect(url_for('.app', app_key=app.key))

    return render_template('edit-application.html',
                           form=form, create=create, app=app)


@views.route('/<regex("[A-Z0-9]+"):app_key>/builds/<build>/')
def build(app_key, build):
    app = get_app(app_key)
    build = db.get_one_or_abort(app.builds.filter_by(tag=build))
    return render_template('build.html', app=app, build=build)


@views.route('/<regex("[A-Z0-9]+"):app_key>/templates/new/',
             methods=['GET', 'POST'], endpoint='new_template')
@views.route('/<regex("[A-Z0-9]+"):app_key>/templates/<int:template_id>/edit/',
             methods=['GET', 'POST'])
@xhr_form
def edit_template(app_key, template_id=None):
    create = template_id is None
    app = get_app(app_key)

    if create:
        template = None
    else:
        template = db.get_one_or_abort(app.templates.filter_by(id=template_id))

    form = forms.TemplateForm(obj=template)

    if form.validate_on_submit():
        session = db.Session()
        if create:
            template = models.DeploymentTemplate(application=app)
        form.populate_obj(template)
        session.add(template)
        session.commit()
        return redirect(url_for('.app', app_key=app.key))

    return render_template('edit-deployment-template.html',
                           form=form, create=create, app=app, tpl=template)


@views.route(
    '/<regex("[A-Z0-9]+"):app_key>/templates/<int:template_id>/delete/',
    methods=['GET', 'POST']
)
@xhr_form
def delete_template(app_key, template_id):
    app = get_app(app_key)
    template = db.get_one_or_abort(app.templates.filter_by(id=template_id))

    form = forms.ConfirmationForm()

    if form.validate_on_submit():
        session = db.Session()
        session.delete(template)
        session.commit()
        return redirect(url_for('.app', app_key=app.key))

    return render_template('confirm-delete-template.html', form=form,
                           tpl=template)


@views.route('/<regex("[A-Z0-9]+"):app_key>/builds/<build>/deploy/',
             methods=['GET', 'POST'])
@xhr_form
def deploy(app_key, build):
    app = get_app(app_key)
    build = db.get_one_or_abort(app.builds.filter_by(tag=build))

    form = forms.DeploymentSetupForm(app)

    if form.validate_on_submit():
        instance = build.deploy(form.data['host'],
                                form.data['template'].template)
        session = db.Session()
        session.add(instance)

        route = Route(instance=instance, routing_key=form.data['hostname'])
        session.add(route)

        client = instance.host.get_client()
        child_ip = get_container_ip(client, instance.container)
        parent_ip = get_container_ip(
            client,
            current_app.config['FRONTEND_NAME']
        )
        allow_traffic(parent_ip, child_ip, 5510)

        session.commit()

        route.update(current_app.config['FRONTEND_NAME'])

        return redirect(url_for('.instance', app_key=app.key,
                                container_id=instance.container[:10]))

    return render_template('deploy-setup.html', form=form, app=app,
                           build=build)


@views.route('/<regex("[A-Z0-9]+"):app_key>/instances/<container_id>/')
def instance(app_key, container_id):
    app = get_app(app_key)
    instance = db.get_one_or_abort(app.instances.filter(
        models.Instance.container.startswith(container_id)))

    return render_template('instance.html', app=app, instance=instance)


@views.route('/<regex("[A-Z0-9]+"):app_key>/instances/<container_id>/stop/',
             methods=['GET', 'POST'])
@xhr_form
def stop(app_key, container_id):
    app = get_app(app_key)
    instance = db.get_one_or_abort(app.instances.filter(
        models.Instance.container.startswith(container_id)))

    form = forms.ConfirmationForm()

    if form.validate_on_submit():
        session = db.Session()
        instance.stop()
        for route in instance.routes:
            route.update(current_app.config['FRONTEND_NAME'])
        session.commit()
        return redirect(url_for('.app', app_key=app.key))

    return render_template('confirm-stop-instance.html', form=form,
                           instance=instance)
