from flask import Blueprint, render_template, redirect, url_for

from deployer import database as db
from deployer.utils import xhr_form
from . import models, forms


views = Blueprint('hosts', __name__, template_folder='templates')


@views.route('/')
def index():
    hosts = db.Session().query(models.Host).all()
    return render_template('hosts.html', hosts=hosts)


@views.route('/<int:host_id>/')
def host(host_id):
    host = db.get_or_abort(models.Host, host_id)
    return render_template('host.html', host=host)


@views.route('/new/', methods=['GET', 'POST'], endpoint='new')
@views.route('/<int:host_id>/edit/', methods=['GET', 'POST'])
@xhr_form
def edit(host_id=None):
    create = host_id is None
    host = None if create else db.get_or_abort(models.Host, host_id)
    form = forms.HostForm(obj=host)

    if form.validate_on_submit():
        session = db.Session()
        if create:
            host = models.Host()
        form.populate_obj(host)
        session.add(host)
        session.commit()
        return redirect(url_for('.host', host_id=host.id))

    return render_template('edit-host.html',
                           form=form, create=create, host=host)
