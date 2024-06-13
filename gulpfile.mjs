import fs from 'fs-extra';
import { src, dest, parallel, series } from 'gulp';
import stylus from 'gulp-stylus';
import pug from 'gulp-pug';
import log from 'gulplog';
import resedit from 'resedit-cli';
import {read} from 'read';

const buildStylus = () =>
    src('./src/bundle.styl')
    .pipe(stylus({
        compress: true,
        'include css': true
    }))
    .pipe(dest('./assets/'));

const buildPug = () =>
    src('./src/index.pug')
    .pipe(pug({
        pretty: false
    }))
    .pipe(dest('./assets/'));

export const build = parallel(buildStylus, buildPug);


const dumpPfx = () => {
    if (!process.env.SIGN_PFX) {
        log.warn('❔ \'dumpPfx\': Cannot find PFX certificate in environment variables. Provide it as a local file at ./CoMiGoGames.pfx or set the environment variable SIGN_PFX.');
        return Promise.resolve();
    }
    return fs.writeFile(
        './CoMiGoGames.pfx',
        Buffer.from(process.env.SIGN_PFX, 'base64')
    );
};

const exePatch = {
    sign: true,
    p12: './CoMiGoGames.pfx'
};
if (process.env.SIGN_PASSWORD) {
    exePatch.password = process.env.SIGN_PASSWORD.replace(/_/g, '');
}

const signInstaller = async () => {
    if (!(await fs.pathExists(exePatch.p12))) {
        log.warn('⚠️  \'signInstaller\': Cannot find PFX certificate. Continuing without signing.');
        delete exePatch.p12;
        exePatch.sign = false;
    } else if (!process.env.SIGN_PASSWORD) {
        log.warn('❔  \'signInstaller\': Cannot find PFX password in the SIGN_PASSWORD environment variable. Assuming manual input.');
        const pass = await read({
            prompt: 'Enter PFX password: (not shown. timing out in 60 seconds.)',
            silent: true,
            timeout: 1000 * 60
        });
        if (!pass) {
            log.warn('⚠️  \'signInstaller\': Cannot find PFX password in the SIGN_PASSWORD environment variable. Continuing without signing.');
            delete exePatch.p12;
            exePatch.sign = false;
        } else {
            exePatch.password = pass;
        }
    }
    if (!exePatch.sign) {
        throw new Error('Cannot find PFX certificate or PFX password.');
    }
    const patchPath = (await fs.pathExists('./dist/ctjsWebInstaller.exe')) ? './dist/ctjsWebInstaller.exe' : './dist/windows/ctjsWebInstaller.exe';
    await resedit({
        in: patchPath,
        out: patchPath,
        ...exePatch
    });
};

export const sign = series(dumpPfx, signInstaller);

export default build;