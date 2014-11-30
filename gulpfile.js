var gulp = require('gulp');

var minifyCss = require('gulp-minify-css');
var ngAnnotate = require('gulp-ng-annotate');
var uglify = require('gulp-uglify');
var rename = require('gulp-rename');

dest = './kotti/static';

gulp.task('copy-vendor', function () {
  // copy some bower components
  gulp.src(['./bower_components/bootstrap/dist/**/*.*',
            '!**/npm.js'],
           {base: './bower_components/bootstrap/dist/'})
    .pipe(gulp.dest(dest));
});

gulp.task('minify-js', function() {
  gulp.src([dest + '/*.js',
            '!' + dest + '/*.min.js'],
           {base: dest})
    .pipe(ngAnnotate())
    .pipe(uglify())
    .pipe(rename({suffix: '.min'}))
    .pipe(gulp.dest(dest));
});

gulp.task('minify-css', function() {
  gulp.src([dest + '/*.css',
            '!' + dest + '/*.min.css'],
           {base: dest})
    .pipe(minifyCss())
    .pipe(rename({suffix: '.min'}))
    .pipe(gulp.dest(dest));
});

// Default task
gulp.task(
  'default', [
    'copy-vendor',
    'minify-js',
    'minify-css'
  ]
);
