# TODO

- [ ] Add argument in update contact to make it automatically update a contact if repeat found
- [ ] Display terminal/output onto browser screen
- [ ] Make sure user logs into their email if info provided on form
- [ ] Get texting to work
  - [X] Implement send text messages
  - [ ] Implement receive text messages
- [ ] Get emailing to work
  - [ ] Implement send email messages
  - [ ] Implement receive email/text messages-WIP!->refactored the receive code to provide more ins/hooks for webapp to use
- [X] Fix url parsing (only make urls attachment if they are pics/video/gif, if just a link than leave it)
  - [X] SOLUTION: used fleep library (see setup script for pip)
- [ ] Send attachments that include env variables (%{VAR}% or ${VAR} or ${VAR})
- [ ] Sending messages longer than 120 with no spaces is stuck in "appending"
- [ ] Add command line flags

## Nice to haves

- [ ] Make contacts private (also prevents duplicate names)
  - [ ] Add different users
  - [ ] each person creates there own account (adds to accounts.json file)
  - [ ] create new form just for adding contacts (placeholders need to say "their..." instead of "your...")
- [ ] contact list drop down menu in "first/last name" input box
  - [ ] If possible use dropdown & text enter at same time
- [ ] Add "Can't find your contact, add them!" button when sending
- [ ] Add drop down menu for sms providers
- [ ] Define low/high level api functions better
- [X] Add ability to press enter when sending messages (keep concatting inputs until keyboard exception- 'control-c')
- [ ] Download all icons/pictures to use locally (saves fetch time)
- [ ] Failed to send D:\\.ssh\id_rsa.pub
- [ ] Fix ./setup.sh for linux to "sudo apt-get install python3-venv" -> otherwise cant create virtual environment
- [ ] Shebang doesnt have '!' in run.sh
- [ ] Get correct python Location for run.sh
- [ ] MATT: make run.bat (same as run.sh) but for windows users
- [ ] Make run.bat go to right spot based on os (/bin) in the emailEnv
- [ ] Fix shebang in run.sh
