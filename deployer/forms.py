from wtforms.form import BaseForm, Form
from wtforms import fields, validators


class RouteForm(Form):
    container = fields.SelectField()
    routing_key = fields.StringField()
    weight = fields.IntegerField(default=1)


def add_route_form(containers, formdata):
    form = RouteForm(formdata)
    choices = []
    for c in containers:
        for n in c['Names']:
            label = '{} ({})'.format(n, c['Tag'])
            choices.append((n, label))
    form.container.choices = choices
    return form


def release_template_form(path, containers, formdata):
    from lxml import etree
    tree = etree.parse(path)

    formfields = {}
    spec = {
        'env': [],
        'ports': [],
        'folders': [],
        'links': [],
    }

    for field in tree.iterfind('.//environment/*'):
        spec['env'].append(field.tag)
        default = field.text or None
        formfields[field.tag] = fields.StringField(field.tag, validators=[
            validators.required(),
        ], default=default)

    for field in tree.iterfind('.//shared-folders/folder'):
        name = field.attrib['mountpoint']
        default = field.attrib.get('local', None)
        spec['folders'].append(name)
        formfields[name] = fields.StringField(name, validators=[
            validators.required()
        ], default=default)

    for field in tree.iterfind('.//ports/expose'):
        type = field.attrib['type']
        container = field.attrib['container']
        label = '{}/{}'.format(type, container)
        name = 'port_{}_{}'.format(type, container)
        spec['ports'].append((name, type, container))
        formfields[name + '_host_ip'] = fields.StringField(label, validators=[
            validators.Optional(),
            validators.IPAddress(),
        ])
        formfields[name + '_host_port'] = fields.IntegerField(
            label,
            validators=[
                validators.Optional(),
                validators.NumberRange(0, 65535),
            ]
        )

    containers_by_repo = {}

    for c in containers:
        try:
            repo, tag = c['Image'].split(':')
        except ValueError:
            continue
        for name in c['Names']:
            if '/' not in name[1:]:
                label = '{} ({})'.format(name[1:], tag)
                containers_by_repo.setdefault(repo, []).append((name, label))

    for field in tree.iterfind('.//links/*'):
        spec['links'].append(field.tag)
        default = field.attrib.get('container', None)

        if 'repository' in field.attrib:
            choices = containers_by_repo.get(field.attrib['repository'], [])

            formfields[field.tag] = fields.SelectField(field.tag, validators=[
                validators.required(),
            ], default=default, choices=choices)
        else:
            formfields[field.tag] = fields.StringField(field.tag, validators=[
                validators.required(),
            ], default=default)

    form = BaseForm(formfields)
    form.process(formdata)

    return form, spec
