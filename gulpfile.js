/*
  Gulp tasks
    - run 'gulp styles' to compile stylesheets.
*/

var gulp = require('gulp');
var sass = require('gulp-sass');
var cssnano = require('gulp-cssnano');
var rename = require('gulp-rename');

// Compile sass into css task
gulp.task('styles', function() {
  gulp.src('sass/main.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(cssnano())
    .pipe(gulp.dest('./app/static/app/content/'));
  gulp.src('sass/pages/app/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(cssnano())
    .pipe(gulp.dest('./app/static/app/content/'));
  gulp.src('sass/pages/experiences/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(cssnano())
    .pipe(gulp.dest('./experiences/static/experiences/content/'));
});

// Pipe compiled js into static folders
gulp.task('itinerary-tool', function() {
  gulp.src('modules/itinerary-tool/build/bundle.js')
    .pipe(rename('itinerary-tool.min.js'))
    .pipe(gulp.dest('experiences/static/experiences/scripts/'));
});

// Watch task
gulp.task('default', function() {
  gulp.watch('sass/**/*.scss', ['styles']);
});
