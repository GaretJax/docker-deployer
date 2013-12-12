from flask import current_app


def register_functions():
    return {
        'code_commit_url': code_commit_url,
    }


def code_commit_url(commit_id):
    return current_app.config['CODE_REPOSITORY_COMMIT_URL'].format(
        commit=commit_id)
