import os

from datetime import datetime

from flask import Blueprint, render_template, request, current_app, redirect
from flask import url_for
from docker import Client

from deployer import forms, utils, routes


views = Blueprint('deployer', __name__, template_folder='templates')


@views.route('/')
def index():
    return render_template('index.html')


@views.route('/builds/<build_tag>/', methods=['GET', 'POST'])
@utils.xhr_form
def make_build(build_tag):
    template_name = 'padi-webshop'
    template_path = os.path.join(
        current_app.config['DATA_ROOT'],
        'release-templates',
        template_name + '.xml'
    )

    client = Client(version="1.6")
    containers = client.containers(trunc=False)

    form, fields = forms.release_template_form(template_path, containers,
                                               request.form)

    if request.method == 'POST' and form.validate():
        pass

    context = {
        'build_tag': build_tag,
        'form': form,
        'fields': fields,
    }

    return render_template('configure-build.html', **context)


@views.route('/instances/')
def instances():
    client = Client(version='1.6')
    containers = []
    deploy_repo = '{}/{}'.format(
        current_app.config['DOCKER_REGISTRY'],
        current_app.config['DOCKER_BUILDS_REPOSITORY'],
    )
    for c in client.containers(trunc=False):
        try:
            repo, tag = c['Image'].split(':')
        except ValueError:
            continue
        if repo == deploy_repo:
            c['Tag'] = tag
            c['Repo'] = repo
            c['Created'] = datetime.fromtimestamp(c['Created'])
            c['Names'] = [n[1:] for n in c['Names']]
            containers.append(c)

    containers.sort(key=lambda c: c['Created'], reverse=True)

    return render_template('instances.html', **{
        'containers': containers,
    })


@views.route('/routing/')
def routing():
    subscriptions = routes.getall(utils.get_frontend_ip(), 1717)
    return render_template('routing.html', subscriptions=subscriptions)


@views.route('/routing/add/', methods=['GET', 'POST'])
def add_route():
    client = Client(version='1.6')
    containers = []

    deploy_repo = '{}/{}'.format(
        current_app.config['DOCKER_REGISTRY'],
        current_app.config['DOCKER_BUILDS_REPOSITORY'],
    )

    for c in client.containers(trunc=False):
        try:
            repo, tag = c['Image'].split(':')
        except ValueError:
            continue
        if repo == deploy_repo:
            c['Tag'] = tag
            c['Repo'] = repo
            c['Created'] = datetime.fromtimestamp(c['Created'])
            c['Names'] = [n[1:] for n in c['Names']]
            containers.append(c)

    form = forms.add_route_form(containers, request.form)

    if request.method == 'POST' and form.validate():
        container_ip = utils.get_container_ip(
            client,
            form.data['container']
        )
        frontend_ip = utils.get_frontend_ip(client)
        routes.add(
            frontend_ip, 5500,
            form.data['routing_key'],
            container_ip, 5510,
            form.data['weight']
        )

        return redirect(url_for('deployer.routing'))

    return render_template('add-route.html', form=form)


@views.route('/routing/<key>/<name>/weight/', methods=['POST'])
def change_weight(key, name):
    ip, port = name.split(':')
    routes.add(
        utils.get_frontend_ip(), 5500,
        key,
        ip,
        int(port),
        int(request.form['weight'])
    )
    return redirect(url_for('deployer.routing'))
