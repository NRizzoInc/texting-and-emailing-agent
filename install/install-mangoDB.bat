@echo off
REM @file: Needed to execute windows command mid bash by install-mangoDB.sh downloading for windows
REM Based on https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows-unattended/
REM accepts arguments:
REM 1st = path to MangoDB Installer
REM 2nd = path of install dir -- extern/MangoDB
REM 3rd = path to mango installation dir -- extern/MangoDB/Server, but not used/does not work

set mangoInstaller=%1
set mangoInstallDir=%2
set mangoInstallationDir=%3

REM Print important information of where user's MangoDB was installed
echo Path to MangoDB Installer: %mangoInstaller%
REM echo Path to MangoDB Installation Folder: %mangoInstallDir%

REM Actually Install MangoDB

REM Line's Purpose
:: Path output log file
:: Path of MangoDB .msi install file that was fetched
:: DOES NOT ACTUALLY WORK!! Path to install downloaded source code & executables -- Default downloads to "C:\Program Files\MongoDB", but instead download in extern folder
:: ADDLOCAL : Download MangoDB Server, Client, and GUI
msiexec.exe ^
            /l*v %mangoInstallDir%\mdbinstall.log ^
            /qb /i %mangoInstaller% ^
            INSTALLLOCATION="%mangoInstallationDir%" ^
            ADDLOCAL="ServerService,Client" ^
            SHOULD_INSTALL_COMPASS="1"

REM Inform user of their downloads' binary paths
echo MangoDB Client Path: "C:\Program Files\MongoDB\Server\4.2\bin\mongo.exe" -- use this to access via command line
echo MangoDB Server/Daemon Path: "C:\Program Files\MongoDB\Server\4.2\bin\mongod.exe"
