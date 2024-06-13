import sys
import os
# from platform import platform
import webview
import requests
import tempfile
import subprocess
import argparse
from zipfile import ZipFile as ZipFile_
from shutil import copy2

# if "win" in platform().lower() and not "darwin" in platform().lower():
#     installDirectoryParent = os.environ["LOCALAPPDATA"]
# else:
#     installDirectoryParent = os.environ["HOME"]
#     if "darwin" in platform().lower():
#         installDirectoryParent = os.path.join(installDirectoryParent, "Applications")

argparser = argparse.ArgumentParser(description='Ct.js installer arguments')
argparser.add_argument('-a', '--autostart', action='store_true', help='Skip "All done" and "Welcome" screens and automatically launch ct.js after downloading it.')
argparser.add_argument('-d', '--destination', help='Predefine installation directory by passing a ct.js folder here. Useful for in-place updates.')
args = argparser.parse_args()

class Vars:
    githubUrl = "https://api.github.com/repos/ct-js/ct-js/releases/latest"
    installFolderName = "ct.js"
    installDirectoryParent = os.environ["LOCALAPPDATA"]
    def installDir():
        if args.destination == None or args.destination == True or args.destination == False:
            return os.path.join(Vars.installDirectoryParent, Vars.installFolderName)
        return args.destination
    tempdir = tempfile.TemporaryDirectory(prefix='ctjsInstaller-')
    downloadedFileName = "ctjs-download.zip"
    downloadedFilePath = lambda: os.path.join(
        Vars.tempdir.name, Vars.installFolderName, Vars.downloadedFileName
    )
    downloadedExtractPath = lambda: os.path.join(
        Vars.tempdir.name, Vars.installFolderName, 'unpacked'
    )

# https://stackoverflow.com/a/13790741
def basePath():
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        basePath = sys._MEIPASS
    except:
        basePath = os.path.abspath(".")
    return basePath
def getAsset(name):
    return os.path.join(basePath(), "assets", name)

def runCommand(command: str):
    print(f"Running command: {command}")
    process = subprocess.Popen(command, shell=True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0 or stderr:
        raise Exception(stderr)

# Download procedure

# https://stackoverflow.com/questions/9419162/download-returned-zip-file-from-url#14260592
def downloadUrl(api: "Api", url):
    prevPercent = 0
    outputPath = Vars.downloadedFilePath()
    print("Downloading " + url + " to " + outputPath)
    try:
        os.mkdir(os.path.dirname(outputPath))
    except:
        pass
    # https://stackoverflow.com/questions/15644964/python-progress-bar-and-downloads#15645088
    try:
        with open(outputPath, "wb") as f:
            response = requests.get(url, stream=True)
            total_length = response.headers.get("content-length")
            if total_length is None:  # no content length header
                f.write(response.content)
            else:
                downloaded = 0
                total_length = int(total_length)
                for data in response.iter_content(chunk_size=1024):
                    downloaded += len(data)
                    f.write(data)
                    done = int(100 * downloaded / total_length)
                    if prevPercent != done:
                        prevPercent = done
                        api.updateDownloadProgress(done)
                    sys.stdout.write("\r[%s / %s]" % (done, 100))
                    sys.stdout.flush()
    except Exception as e:
        api.panic(f'Downloading {url} failed: ' + repr(e) + '\nMaybe try again?')
# Unpacking

# https://stackoverflow.com/a/39296577
class ZipFile(ZipFile_):
    def extractall(self, path=None, members=None, pwd=None):
        if members is None:
            members = self.namelist()
        if path is None:
            path = os.getcwd()
        else:
            path = os.fspath(path)
        for zipinfo in members:
            self.extract(zipinfo, path, pwd)
# https://lukelogbook.tech/2018/01/25/merging-two-folders-in-python/
def copytree(src, dst):
    for src_dir, dirs, files in os.walk(src):
        dst_dir = src_dir.replace(src, dst, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            copy2(src_file, dst_dir)
# JS API

class Api:
    window: "webview.window"
    def __init__(self):
        self.state = 'idle'
    def getInstallDir(self):
        return Vars.installDir()
    def getArch(self):
        return {
            "x64": sys.maxsize > 2 ** 32
        }
    def promptInstallFolder(self):
        Vars.installDirectoryParent = window.create_file_dialog(dialog_type=webview.FOLDER_DIALOG)[0]
        return Vars.installDir()
    def getGithubData(self):
        githubData = requests.get(Vars.githubUrl).json()
        return githubData
    def startDownload(self, url):
        if self.state == 'idle':
            self.state = 'downloading'
            downloadUrl(self, url)
    def unpack(self):
        with ZipFile(Vars.downloadedFilePath(), "r") as zip_ref:
            try:
                zipFolderName = os.path.dirname(zip_ref.namelist()[0])
            except:
                pass
            zip_ref.extractall(Vars.downloadedExtractPath()) # Extract to a temp directory
        # remove old ct.js installation
        if (os.path.exists(Vars.installDir())):
            try:
                os.remove(Vars.installDir())
            except Exception as e:
                self.panic(f'Cannot remove old installation at {Vars.installDir()}: ' + repr(e) + '\nMaybe try running as admin?')
                return
        try:
            copytree(os.path.join(Vars.downloadedExtractPath(), zipFolderName), Vars.installDir())
        except OSError as e:
            self.panic(f'Cannot install to {Vars.installDir()}: ' + repr(e) + '\nMaybe try running as admin?')
            return
    def createShortcuts(self):
        try:
            with open(getAsset("createShortcuts.bat"), "r") as f:
                contents = f.read().replace("{installDir}", Vars.installDir())
            runCommand(contents)
        except Exception as e:
            self.panic('We couldn\'t create shortcuts due to this reason: ' + repr(e) + f'\nStill, ct.js is already successfully installed at {Vars.installDir()}.')
        window.confirm_close = False
    def runCt(self):
        subprocess.Popen([os.path.join(Vars.installDir(), 'ctjs.exe')])
        window.confirm_close = False
        self.quit()
    def updateDownloadProgress(self, progress):
        window.evaluate_js('window.signals.downloadProgress('+ str(progress) +');')
    def canAutostart(self):
        return args.autostart == True
    def panic(self, message = ''):
        window.evaluate_js('window.signals.panic("'+ message.replace('"', '\\"').replace('\n', '\\n') +'");')
    def quit(self):
        window.destroy()
        exit()
# Run the app

if __name__ == '__main__':
    api = Api()
    frozen = getattr(sys, "frozen", False)
    if frozen:
        page = 'index.html'
    else:
        page = 'assets/index.html'
        # Vars.githubUrl = "https://api.github.com/repos/CosmoMyzrailGorynych/random-test-stuff/releases/latest"
    window = webview.create_window('Ct.js installer', page, js_api=api, width=600, height=420, resizable=False, confirm_close=True, shadow=True)
    webview.start(debug=not frozen)
