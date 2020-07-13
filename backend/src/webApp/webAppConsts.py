"""
    @File: Manages common variables shared between webApp files
"""

import os
from .. import utils

pathToThisDir = os.path.dirname(os.path.abspath(__file__))
srcDir = os.path.join(pathToThisDir, "..")
backendDir = os.path.join(srcDir, "..")
userDataDir = os.path.join(backendDir, "userData")
cookieDataPath = os.path.join(userDataDir, "cookies.json")
rootDir = os.path.join(backendDir, "..")
frontendDir = os.path.join(rootDir, "frontend")
staticDir = os.path.join(frontendDir, "static")
htmlDir = os.path.join(frontendDir, "htmlTemplates")
urls = utils.loadJson(os.path.join(staticDir, "urls.json"))
sites = urls["sites"]
formSites = urls["formSites"]
infoSites = urls["infoSites"]
settingsSites = urls["settingsSites"]