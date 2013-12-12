import os
import argparse


def load_config(args):
    os.environ.setdefault('DEPLOYER_FRONTEND_NAME', 'padi_sportswear_frontend')

    if args.debug:
        os.environ['DEPLOYER_DEBUG'] = '1'
        os.environ.setdefault('DEPLOYER_SECRET_KEY', 'changeme')
    elif 'DEPLOYER_DEBUG' in os.environ:
        del os.environ['DEPLOYER_DEBUG']

    os.environ['DEPLOYER_DATABASE'] = args.database

    if args.no_init_db:
        os.environ['DEPLOYER_NO_INIT_DB'] = '1'


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-i', '--interface', default='127.0.0.1')
    parser.add_argument('--no-init-db', action='store_true')
    parser.add_argument('database')
    return parser


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def main():
    parser = get_parser()
    args = parser.parse_args()
    load_config(args)

    cmdargs = [
        '--master',
        # If we set these to
        #'--uid', 'uwsgi',
        #'--gid', 'uwsgi',
        '--workers', '4',
        '--auto-procname',
        '--need-app',
        '--enable-threads',
        '--wsgi', 'padi.wsgi',
        '--http', '{}:5000'.format(args.interface),
        '--module', 'deployer.app',
        '--callable', 'app',
        '--cache2', 'name=application,items=100',
        '--cache2', 'name=mappings,items=100',
    ]

    if args.debug:
        cmdargs.extend([
            '--py-autoreload', '1',
            '--catch-exceptions',
            '--workers', '1',
            '--threads', '4',
            '--single-interpreter',
        ])

        print '=' * 40
        print ' WARNING: Running in DEBUG mode'
        print '=' * 40
        print

    path = which('uwsgi')

    if not path:
        raise RuntimeError('uWSGI executable not found on path.')

    print 'Found uwsgi at "{}"'.format(path)
    os.execv(path, cmdargs)
