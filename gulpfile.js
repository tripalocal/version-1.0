/*
  Gulp tasks
    - run 'gulp styles' to compile stylesheets.
*/

var gulp = require('gulp');
var sass = require('gulp-sass');
var cssnano = require('gulp-cssnano');
var rename = require('gulp-rename');
var browserSync = require('browser-sync').create();

// Compile sass into css task
gulp.task('styles', function() {
  gulp.src('sass/main.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(cssnano())
    .pipe(gulp.dest('./app/static/app/content/'))
    .pipe(browserSync.stream());
  gulp.src('sass/pages/app/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(cssnano())
    .pipe(gulp.dest('./app/static/app/content/'))
    .pipe(browserSync.stream());
  gulp.src('sass/pages/experiences/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(cssnano())
    .pipe(gulp.dest('./experiences/static/experiences/content/'))
    .pipe(browserSync.stream());
});

// Pipe compiled js into static folders
gulp.task('itinerary-tool', function() {
  gulp.src('modules/itinerary-tool/build/bundle.js')
    .pipe(rename('itinerary-tool.min.js'))
    .pipe(gulp.dest('experiences/static/experiences/scripts/'));
});

// Watch task
gulp.task('default', function() {
  browserSync.init({
    proxy: '127.0.0.1:8000',
    online: true
  })
  gulp.watch('sass/**/*.scss', ['styles']);
  gulp.watch('app/templates/app/*.html').on('change', browserSync.reload)
  gulp.watch('experiences/templates/experiences/*.html').on('change', browserSync.reload)
});
