## Customise local environment
In order to get rid of stash and unstashes, here is a better practice to customise your development environment.

1. Create `local_settings.py` under project root.
2. Override `DATABASES` or anything you like.
3. Append `DEVELOPMENT = True` to the file if you would like turn off Mixpanel or other live server specific settings.

	For example, if program crashes because of the use of `settings.MIXPANEL_TOKEN` and you don't have it on your localenviroment. Simply add
	
	`if not settings.DEVELOPMENT:` 
	
	before the code.
	
## Organise static files

### Global static files
1. Global static files go into `/images/css`, `/images/js`, `/images/img`.
2. Reference using `{{ MEDIA_URL }}img/tripalocal_Logo.png`

### App specific static files
1. App specific files go into `<app_name>/static/<app_name>/...`.
2. In template, reference static files using `{% static '<app_name>/...' %}`.
3. In CSS, reference static files using `background: url('../img/foo.png');`.
4. Remember to run `python manage.py collectstatic`.