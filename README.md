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

### Turn on S3
To turn on S3, add DEFAULT_FILE_STORAGE, STATICFILES_STORAGE ENV variables:

In Mac OS, do it like this:

`DEFAULT_FILE_STORAGE=custom_storages.MediaStorage`
`STATICFILES_STORAGE=custom_storages.StaticStorage`

## Stylesheets
### Compiling sass
(Make sure you have npm installed. Then install dependencies with `npm install`)  

- `gulp styles` will compile the sass code in `/sass` into a single `main.css` along with page specific sass files and placed in their respective folders minified.  
- `gulp` will run an even listener that autocompiles your sass stylesheets every time you save.  

No need to upload the `/sass` directory to the live site.

### CSS Structure
The architecture of the stylesheets cascades as follows:  
*Bootstrap -> Sass library -> Page specific styles*  

When implementing new UI components, have a look at what can be used from Bootstrap's docs, followed by components/layouts in our sass library, and then finally in the page specific styles.  

** It is best practice to define reusable components, and of course, reuse them.**  
Partial files begin with an underscore and will be ignored by the compiler. List them in main.scss to be compiled.
