@echo off
REM @file: Needed to execute windows command mid bash by install-mangoDB.sh downloading for windows
REM accepts arguments:
REM 1st = path to download
echo Path to MangoDB Install: %1
msiexec.exe /l*v mdbinstall.log /qb /i %1