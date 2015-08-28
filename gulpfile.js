/*
  Gulp tasks
    - run 'gulp styles' to compile stylesheets.
*/

var gulp = require('gulp');
var sass = require('gulp-sass');
var minifyCss = require('gulp-minify-css');

// Compile sass into css task
gulp.task('styles', function() {
  gulp.src('sass/main.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(minifyCss())
    .pipe(gulp.dest('./app/static/app/content/'));
  gulp.src('sass/pages/app/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(minifyCss())
    .pipe(gulp.dest('./app/static/app/content/'));
  gulp.src('sass/pages/experiences/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(minifyCss())
    .pipe(gulp.dest('./experiences/static/experiences/content/'));
});

// Watch task
gulp.task('default', function() {
  gulp.watch('sass/**/*.scss', ['styles']);
});
