## Customise local environment
In order to get rid of stash and unstashes, here is a better practice to customise your development environment.

1. Create `local_settings.py` under project root.
2. Override `DATABASES` or anything you like.
3. Append `DEVELOPMENT = True` to the file if you would like turn off Mixpanel or other live server specific settings.

	For example, if program crashes because of the use of `settings.MIXPANEL_TOKEN` and you don't have it on your localenviroment. Simply add
	
	`if not settings.DEVELOPMENT:` 
	
	before the code.
	