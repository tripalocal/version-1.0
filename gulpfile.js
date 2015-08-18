/*
  Gulp tasks
    - run 'gulp styles' to compile stylesheets.
*/

var gulp = require('gulp');
var sass = require('gulp-sass');

// Compile sass into css task
gulp.task('styles', function() {
  gulp.src('sass/**/*.scss')
    .pipe(sass().on('error', sass.logError))
    .pipe(gulp.dest('./app/static/app/content/'));
});

// Watch task
gulp.task('default', function() {
  gulp.watch('sass/**/*.scss', ['styles']);
});
