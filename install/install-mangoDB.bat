@echo off
REM @file: Needed to execute windows command mid bash by install-mangoDB.sh downloading for windows
REM Based on https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows-unattended/
REM accepts arguments:
REM 1st = path to download
REM 2nd = name of install dir -- something like "Server" -- based on recommendations

set installExecutable=%1
set mangoInstallDirname=%2
REM root/extern/MangoDB -- path to download's directory
for %%F in (%installExecutable%) do set installExecDir=%%~dpF
REM root/extern/mangoDB/Server
set installMangoPath=%installExecDir%\%mangoInstallDirname%\

REM Print important information of where user's MangoDB was installed
echo Path to MangoDB Installer: %installExecutable%
echo Path to MangoDB Install: %installMangoPath%

REM Actually Install MangoDB

REM Line's Purpose
:: Path output log file
:: Path of MangoDB .msi install file that was fetched
:: Path to install downloaded source code & executables -- Default downloads to "C:\Program Files\MongoDB", but instead download in extern folder
:: Download MangoDB Server, Client, and GUI
msiexec.exe ^
            /l*v %installExecDir%\mdbinstall.log ^
            /qb /i %installExecutable% ^
            INSTALLLOCATION="%installMangoPath%" ^
            ADDLOCAL="ServerService,Client" ^
            SHOULD_INSTALL_COMPASS="1"

REM Start MangoDB to Create the Database

