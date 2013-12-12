def release_dockerfile(build_repo, build_tag, env, fileobj=None):
    s = []
    s.append('FROM {}:{}'.format(build_repo, build_tag))

    for k, v in env.iteritems():
        s.append('ENV {} {}'.format(k, v))

    # TODO: These are unset from the previous build runs, but this is a bug
    #       which should be fixed in docker. This is inly a temporary
    #       workaround.
    s.append('ENTRYPOINT ["django-admin.py"]')
    s.append('CMD ["runuwsgi"]')

    return '\n'.join(s)
