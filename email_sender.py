import os
import sys
import json
import smtplib
import pprint
import getpass
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template # needed to send a template txt file
path_to_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path_to_this_dir)

class email_sender():
    def __init__(self):
        '''
            This class is responsible for sending emails 
        '''
        self.message_templates_dir = os.path.join(path_to_this_dir, "message_templates")
        self.path_to_contact_list = os.path.join(path_to_this_dir, "contacts.json")
        self.contact_list = self.load_json()
        self.email_providers_info = self.load_json(os.path.join(path_to_this_dir, 'email_providers_info.json'))
        print("The current contact list is:\n")
        pprint.pprint(self.contact_list)

    def send_email(self, contact_info, content=None, type_of_msg='default', to_phone_num=False):
        '''
            Args:
                'type_of_msg' represents the email template name
                'to_phone_num' represents wheter or not the message should be sent to the person's email to phone number.
                    \n(Set to_phone_num to true to send it to their phone number)
        '''

        # Based on input about which email service provider the user wants to login to determine info for server
        lower_case_list = list(map(lambda x:x.lower(), self.email_providers_info.keys()))
        dict_keys_mapped_to_list = list(map(lambda x:x, self.email_providers_info.keys()))
        print("The available list of providers you can login to is: \n{0}".format(list(self.email_providers_info.keys())))

        email_service_provider = input("\nWhich email service provider do you want to login to: ")
        found_valid_email_provider = False
        email_service_provider_info = {}
        
        while found_valid_email_provider is False:
            # see if email service provider exists in the list (case-insensitive)- use lambda function to turn list to lowercase
            if email_service_provider.lower() in lower_case_list:
                # get the index of name match in the list (regardless of case)
                index = lower_case_list.index(email_service_provider.lower())

                # Using the index of where the correct key is located, use the dict which contains all entries of original dict to get exact key name
                dict_key_name = dict_keys_mapped_to_list[index]

                # Get the information pertaining to this dict key
                email_service_provider_info = self.email_providers_info[dict_key_name ]
                found_valid_email_provider = True
            else:
                print("The desired email service provider not supported! Try using another one")
            

        self.connect_to_email_server(email_service_provider_info)
        msg = self.compose_email_msg(type_of_msg)
        
        # send the message via the server set up earlier.
        self.email_server.send_message(msg, content, to_phone_num, email_service_provider_info)
        del msg
        self.email_server.quit()
        print("Successfully sent the email/text")
        

    def compose_email_msg(self, type_of_msg, content, to_phone_num, email_service_provider_info):
        '''
            This function is responsible for composing the email message that get sent out
            \nReturn:

            -The sendable message
        '''
        # create the body of the email to send
        if type_of_msg == "default" and content == None:
            path_to_template_file = os.path.join(self.message_templates_dir, "test_msg.txt")
        
            # read in the content of the text file to send as the body of the email
            msg_template = self.read_template(path_to_template_file)
            reciever = str(contact_info['first_name']) + str(contact_info['last_name'])
            sendable_msg = msg_template.substitute(receiver_name=reciever, sender_name=self.my_email_address) 
        
        elif content != None:
            sendable_msg = content

        # TODO create other elif statements for different cases
        
        # Default to default file 
        else:
            path_to_template_file = os.path.join(self.message_templates_dir, "default.txt")
            sendable_msg = self.read_template(path_to_template_file)

        print("Sending message:\n{0}".format(sendable_msg))


        msg = MIMEMultipart() # create a message object
        # setup the parameters of the message
        msg['From'] = self.my_email_address
        # if set to true then send to phone number with special @ for service provider
        if to_phone_num == True:
            receiver_carrier = contact_info['carrier'].lower()
            
            send_email = False # eventually set based on circumstances to see if user needs to send and email instead of text

            # Check if this email provider allows emails to be sent to phone numbers
            if receiver_carrier in self.email_providers_info.keys().lower():
                index_in_list_of_carrier = [x.lower() for x in self.email_providers_info.keys()].index(receiver_carrier)
                if 'special_address' not in self.email_providers_info[index_in_list_of_carrier].keys():
                    print("Sending text messages through email is not possible when the reciever uses this email provider")
                    send_email = input("Do you want to send an email instead (y/n): ")
                    if send_email.lower() == 'y':
                        send_email = True
                    else:
                        return # end function since cant send text or email

                else:
                    special_at_sign = email_service_provider_info['special_address']

            # if send_email never changed then continue to send the message via text
            if send_email is False: 
                msg['To'] = "{0}@{1}".format(contact_info['phone_num'], special_at_sign) 
            else:
                msg['To'] = contact_info['email'] # send message as if it were a text

        # otherwise just send it to their email
        else:
            msg['To'] = contact_info['email']

        msg['Subject'] = "This is a test"

        # add in the message body
        msg.attach(MIMEText(sendable_msg, 'plain'))
        return msg


    def read_template(self, path_to_file):
        with open(path_to_file, 'r+', encoding='utf-8') as template_file:
            template_file_content = template_file.read()
        return Template(template_file_content)

    def get_contact_info(self, my_first_name, my_last_name):
        '''
            This function will search the existing database for entries with the input first_name and last_name.\n

            Returns:\n
                Dictionary of format: {first name, last name, email, carrier, phone number}
                The phone number return accepts common type of seperaters or none (ex: '-')             
        '''

        contact_info_dict = {}
        email = ''
        phone_num = ''
        carrier = ''

        # Go through the list looking for name matches (case-insensitive)
        for last_name in self.contact_list.keys():
            print(last_name)
            for first_name in self.contact_list[last_name].keys():
                print(first_name)
                if first_name.lower() == my_first_name.lower() and last_name.lower() == my_last_name.lower():
                    print("\nFound a match!\n")
                    contact_first_name = first_name
                    contact_last_name = last_name
                    # stores contact information in the form {"email": "blah@gmail.com", "carrier":"version"}
                    contact_info_dict = self.contact_list[last_name][first_name]
                    email = contact_info_dict['email']
                    phone_num = contact_info_dict['phone_number']
                    carrier = contact_info_dict['carrier']

        # if values were not initialized then no match was found
        if email == '' and phone_num == '' and carrier == '':
            print("Contact does not exist!")
        
        print("Based on the inputs of: \nfirst name = {0} \nlast name = {1}\n".format(my_first_name, my_last_name))
        print("The contact found is:\n{0} {1}\nEmail Address: {2}\nCarrier: {3}\nPhone Number: {4}".format(
            contact_first_name, contact_last_name, email, carrier, phone_num))

        dict_to_return = {
            'first_name' : contact_first_name,
            'last_name': contact_last_name,
            'email': email,
            'carrier': carrier,
            'phone_num' : phone_num
        }

        return dict_to_return

    def connect_to_email_server(self, email_service_provider_info):
        '''
            This function is responsible for connecting to the email server.
            Args:
                - email_service_provider_info: contains information about host address and port # of email server
        '''
        # Get email login
        self.my_email_address = input("Enter your email address: ")
        password = getpass.getpass(prompt="Password for user {0}: ".format(self.my_email_address))

        host_addr = email_service_provider_info['host_address']
        port_num = email_service_provider_info['port_num']

        # Establish connection to email server using self.my_email_address and password given by user
        print("Connecting to smtp email server")
        self.email_server = smtplib.SMTP(host=host_addr, port=int(port_num))
        self.email_server.starttls()
        # Try to login to email server, if it fails then catch exception
        try:
            self.email_server.login(self.my_email_address, password)
        except Exception as error:
            if '535' in str(error):
                # Sometimes smtp servers wont allow connection becuase the apps trying to connect are not secure enough
                # TODO make connection more secure
                print("\nCould not connect to email server because of error:\n{0}\n".format(error))
                print("Try changing your account settings to allow less secure apps to allow connection to be made.")
                print("Quiting program, try connecting again with correct email/password, after making the changes, or trying a different email")
            else:
                print("Encountered error while trying to connect to email server: \n{0}".format(error))
            quit()

    def load_json(self, path_to_json=None):
        if path_to_json == None:
            path_to_json = self.path_to_contact_list

        with open(path_to_json, 'r+') as read_file:
            data = json.load(read_file)
        return data
    
    def add_contacts_to_contacts_list(self, first_name, last_name, email, carrier, phone_num):
        '''
            This function is responsible for adding another contact to the contact list
            Args:\n
                first_name: first name of the person being added
                last_name: last name of the person being added
                email: email of the person being added
                carrier: carrier of the person being added
                phone_num: phone number of the person being added
        '''
        
        # Regardless of where the data gets added, it should be the same 
        common_data_dict = {
            'email': email,
            'carrier': carrier,
            'phone_number': phone_num
        }

        # store existing contact list so it can be modified
        new_contact_list = self.contact_list

        # check to see if the person's last name already exists.
        # If so just modify it instead  of creating an entirely new last name section
        if last_name in new_contact_list.keys():
            new_contact_list[last_name][first_name] = common_data_dict
        
        # If last name doesnt exist in contact list yet, then add it
        else:
            new_contact_list[last_name] = {}
            new_contact_list[last_name][first_name] = common_data_dict

        # write updated version of contact list to the json file
        with open(self.path_to_contact_list, 'w+') as write_file:
            json.dump(new_contact_list, write_file, indent=4)

        # Update existing variable used by rest of program so it constantly stays up to date
        self.contact_list = new_contact_list
        print("The updated contacts list is:\n")
        pprint.pprint(self.contact_list)


if __name__ == "__main__":
    email = email_sender()

    #if user doesnt give an input then use defaults
    if len(sys.argv) == 1: # there will always be at least 1 argument (the name of the python script)
        contact_info = email.get_contact_info('nick', 'rizzo')
    
    # If user gives input use those values
    else:
        if len(sys.argv) < 2: print("Invalid number of arguments entered!")
        else:
            # Get arguments from when script is called
            first_name = sys.argv[1]
            last_name = sys.argv[2]
            contact_info = email.get_contact_info(first_name, last_name)
    
    email.send_email(contact_info)


    


