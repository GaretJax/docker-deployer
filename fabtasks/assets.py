from fabric.api import task, local


@task
def watch_styles():
    local('compass watch -c deployer/assets/sass/config.rb')


@task
def compile_styles():
    local('compass compile -c deployer/assets/sass/config.rb')


@task
def watch_scripts():
    local('coffee -c -w -j deployer/static/scripts/master.js '
          'deployer/assets/coffeescripts')


@task
def compile_scripts():
    local('coffee -c -j deployer/static/scripts/master.js '
          'deployer/assets/coffeescripts')


@task
def livereload():
    print 'To livereload your web pages add the following script tag to your HTML:'
    print ''
    print '    <script type="text/javascript" src="http://dev:35729/livereload.js"></script>'
    print ''
    local('livereload')