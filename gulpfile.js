const path = require('path'),
      gulp = require('gulp'),
      stylus = require('gulp-stylus'),
      pug = require('gulp-pug');

const buildStylus = () =>
    gulp.src('./src/bundle.styl')
    .pipe(stylus({
        compress: true,
        'include css': true
    }))
    .pipe(gulp.dest('./assets/'));

const buildPug = () =>
    gulp.src('./src/index.pug')
    .pipe(pug({
        pretty: false
    }))
    .pipe(gulp.dest('./assets/'));

const build = gulp.parallel(buildStylus, buildPug);

exports.buildStylus = buildStylus;
exports.buildPug = buildPug;
exports.default = build;