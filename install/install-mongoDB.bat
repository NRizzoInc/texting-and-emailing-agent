@echo off
REM @file: Needed to execute windows command mid bash by install-mongoDB.sh downloading for windows
REM Based on https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows-unattended/
REM accepts arguments:
REM 1st = path to mongoDB Installer
REM 2nd = path of install dir -- extern/mongoDB
REM 3rd = path to mongo installation dir -- extern/mongoDB/Server, but not used/does not work
REM 4th = path to mongo client
REM tth = path to mongo daemon executable

set mongoInstaller=%1
set mongoInstallDir=%2
set mongoInstallationDir=%3
set mongoClientPath=%4
set mongoDaemonPath=%5

REM Print important information of where user's mongoDB was installed
echo Path to mongoDB Installer: %mongoInstaller%
REM echo Path to mongoDB Installation Folder: %mongoInstallDir%

REM Actually Install mongoDB

REM Line's Purpose
:: Path output log file
:: Path of mongoDB .msi install file that was fetched
:: DOES NOT ACTUALLY WORK!! Path to install downloaded source code & executables -- Default downloads to "C:\Program Files\MongoDB", but instead download in extern folder
:: ADDLOCAL : Download mongoDB Server, Client, and GUI
msiexec.exe ^
            /l*v %mongoInstallDir%\mdbinstall.log ^
            /qb /i %mongoInstaller% ^
            INSTALLLOCATION="%mongoInstallationDir%" ^
            ADDLOCAL="ServerService,Client" ^
            SHOULD_INSTALL_COMPASS="1"

REM Inform user of their downloads' binary paths
echo mongoDB Client Path: %mongoClientPath% -- use this to access via command line
echo mongoDB Server/Daemon Path: %mongoDaemonPath%
