# post-deploy tasks
postdeploy: bash bin/post_deploy

# Run web app
web: gunicorn --chdir src config.wsgi:application --log-file - --timeout 120

# Run celery worker
workerweb: celery --workdir src -A config worker -l info -Q celery --pool threads
