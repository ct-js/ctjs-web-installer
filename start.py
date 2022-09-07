import sys
import os
# from platform import platform
import webview
import requests
from os import path
import tempfile
from zipfile import ZipFile as ZipFile_
from zipfile import ZipInfo

# if "win" in platform().lower() and not "darwin" in platform().lower():
#     installDirectoryParent = os.environ["LOCALAPPDATA"]
# else:
#     installDirectoryParent = os.environ["HOME"]
#     if "darwin" in platform().lower():
#         installDirectoryParent = os.path.join(installDirectoryParent, "Applications")

class Vars:
    githubUrl = "https://api.github.com/repos/ct-js/ct-js/releases/latest"
    installFolderName = "ct.js"
    installDirectoryParent = os.environ["LOCALAPPDATA"]
    installDir = lambda: os.path.join(Vars.installDirectoryParent, Vars.installFolderName)
    downloadedFileName = "ctjs-download.zip"
    downloadedFilePath = lambda: os.path.join(
        tempfile.gettempdir(), Vars.installFolderName, Vars.downloadedFileName
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
    import subprocess
    subprocess.Popen(command, shell=True)

# Download procedure

# https://stackoverflow.com/questions/9419162/download-returned-zip-file-from-url#14260592
def downloadUrl(app: "Api", url, save_path="", chunk_size=1024):
    if save_path == "":
        save_path = Vars.downloadedFilePath()

    prevMessageChange = 0

    print("Downloading " + url + " to " + save_path)
    try:
        os.mkdir(os.path.dirname(save_path))
    except:
        pass
    # https://stackoverflow.com/questions/15644964/python-progress-bar-and-downloads#15645088
    with open(save_path, "wb") as f:

        response = requests.get(url, stream=True)
        total_length = response.headers.get("content-length")

        if total_length is None:  # no content length header
            f.write(response.content)
        else:
            progressBarTotal = 100
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=chunk_size):
                dl += len(data)
                f.write(data)
                done = int(progressBarTotal * dl / total_length)
                if prevMessageChange != done:
                    prevMessageChange = done
                    app.updateDownloadProgress(done)
                sys.stdout.write("\r[%s / %s]" % (done, progressBarTotal))
                sys.stdout.flush()
                try:
                    app.pbar.setValue(done)
                except:
                    pass


# JS API

class Api:
    def __init__(self):
        self.state = 'idle'
    def startDownload(self):
        if self.state == 'idle':
            self.state = 'downloading'
            downloadUrl(self, )
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
    def finishDownload(self):
        window.evaluate_js('window.signals.trigger(\'downloadComplete\')')
    def updateDownloadProgress(self, progress):
        window.evaluate_js('window.signals.trigger(\'downloadProgress\', '+ progress +')')
    def abort(self):
        window.destroy()
# Run the app

if __name__ == '__main__':
    api = Api()
    frozen = getattr(sys, "frozen", False)
    if frozen:
        page = 'index.html'
    else:
        page = 'assets/index.html'
    window = webview.create_window('Ct.js installer', page, width=600, height=420, js_api=api)
    webview.start(debug=not frozen)

