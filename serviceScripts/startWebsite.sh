#!/bin/bash
# this script starts up the website in a background process that will live on even after ssh logout

alias startWebApp="sudo systemctl start email-web-app.service"
$startWebApp
