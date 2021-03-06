/*
   Gulp tasks
    - run 'gulp' to start browserSync while watching for changes.
    - run 'gulp styles' to compile stylesheets.
    - run 'gulp itinerary-tool' to compile itinerary tool.
*/

var gulp = require('gulp');
var sass = require('gulp-sass');
var cssnano = require('gulp-cssnano');
var rename = require('gulp-rename');
var exec = require('child_process').exec;
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

// compile itinerary tool
gulp.task('compile-itinerary-tool', function(callback) {
  process.chdir('modules/itinerary-tool');
  exec('npm run build', function(err, stdout, stderr) {
    console.log(stdout);
    console.log(stderr);
    process.chdir('../../');
    callback(err);
  });
})

// Pipe compiled js into static folders
gulp.task('itinerary-tool', ['compile-itinerary-tool'], function() {
  console.log('Copying bundle.js to static/experiences/scripts/itinerary-tool.min.js')
  gulp.src('modules/itinerary-tool/build/bundle.js')
    .pipe(rename('itinerary-tool.min.js'))
    .pipe(gulp.dest('experiences/static/experiences/scripts/'))
    .pipe(browserSync.stream());
});

// Watch task
gulp.task('default', function() {
  browserSync.init({
    proxy: '127.0.0.1:8000',
    online: true
  })
  gulp.watch('sass/**/*.scss', ['styles']);
  gulp.watch('modules/itinerary-tool/app/**/*.js', ['itinerary-tool']);
  gulp.watch('app/templates/app/*.html').on('change', browserSync.reload);
  gulp.watch('experiences/templates/experiences/*.html').on('change', browserSync.reload);
});
