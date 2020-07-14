# TODO

- [ ] have webApp auto log out email after some time (currently stays logged in indefinitely, which causes error in backend at timeout)
  - [ ] make sure emailAgent handles that correctly & sets everything
  - [ ] if user is idle on page > 3 min, auto redirect to mainpage with alert describing why
- [ ] Dont store data in python memory
  - [ ] Create a database (hopefully a native python one exists or use mangoDB and add setup script)
- [ ] Add argument in update contact to make it automatically update a contact if repeat found
- [ ] Make sure user logs into their email if info provided on form
- [ ] Get emailing to work
  - [ ] Implement send email messages
  - [ ] Implement receive email/text messages-WIP!->refactored the receive code to provide more ins/hooks for webapp to use
- [ ] Send attachments that include env variables (%{VAR}% or ${VAR} or ${VAR})
- [ ] Sending messages longer than 120 with no spaces is stuck in "appending"

## Nice to haves

- [ ] Make nicer landing page
  - [ ] Explain that webApp's account not linked to actual email and that I do not save your email's login for security reasons
- [ ] Pretty up webApp kludges for receiving
  - [ ] FlaskForms do not match send/receive/add style
  - [ ] Flash messages are bulleted and look strange
    - [ ] Put in a div and have js event listener parse it and create alerts
- [ ] contact list drop down menu in "first/last name" input box
  - [ ] If possible use dropdown & text enter at same time
- [ ] Add "Can't find your contact, add them!" button when sending
- [ ] Add drop down menu for sms providers
- [ ] Define low/high level api functions better
- [X] Add ability to press enter when sending messages (keep concatting inputs until keyboard exception- 'control-c')
- [ ] Download all icons/pictures to use locally (saves fetch time)
- [ ] Failed to send D:\\.ssh\id_rsa.pub
- [ ] MATT: make run.bat (same as run.sh) but for windows users
- [ ] login via CLI
