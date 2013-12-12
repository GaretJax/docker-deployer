import pprint as _pprint
import json


__all__ = ['pprint', 'format_json']


def pprint(obj):
    return _pprint.pformat(obj)


def format_json(obj):
    return json.dumps(obj, indent=4, sort_keys=True)
