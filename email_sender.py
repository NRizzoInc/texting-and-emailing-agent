'''
    Need to pip:
        pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
'''
#TODO: If contact list has multiple emails, allow user to pick
import os
import sys
import json
import pprint
import getpass
# Email imports
import smtplib
import ssl
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

    def send_email(self, receiver_contact_info):
        '''
            
        '''

        # Based on input about which email service provider the user wants to login to determine info for server
        lower_case_list = list(map(lambda x:x.lower(), self.email_providers_info.keys()))
        dict_keys_mapped_to_list = list(map(lambda x:x, self.email_providers_info.keys()))
        
        found_valid_email_provider = False
        email_service_provider_info = {}

        while found_valid_email_provider is False:
            print("The available list of providers you can login to is: \n{0}".format(list(self.email_providers_info.keys())))
            email_service_provider = input("\nWhich email service provider do you want to login to: ")

            # see if email service provider exists in the list (case-insensitive)- use lambda function to turn list to lowercase
            if email_service_provider.lower() in lower_case_list:
                # get the index of name match in the list (regardless of case)
                index = lower_case_list.index(email_service_provider.lower())

                # Using the index of where the correct key is located, use the dict which contains all entries of original dict to get exact key name
                dict_key_name = dict_keys_mapped_to_list[index]

                # Get the information pertaining to this dict key
                email_service_provider_info = self.email_providers_info[dict_key_name]
                found_valid_email_provider = True
            else:
                print("The desired email service provider not supported! Try using another one")
            

        self.connect_to_email_server(email_service_provider_info['host_address'], email_service_provider_info['port_num'])
        msg = self.compose_msg(email_service_provider_info, receiver_contact_info)
        
        # send the message via the server set up earlier.
        if msg is None: # will only be None if can't send email or text
            print("Could not send an email or text message")
        else:
            self.email_server.send_message(msg)
            print("Successfully sent the email/text to {0} {1}".format(receiver_contact_info['first_name'], receiver_contact_info['last_name']))
        self.email_server.quit()
        

    def compose_msg(self, email_service_provider_info, receiver_contact_info):
        '''
            This function is responsible for composing the email message that get sent out
            \nReturn:

            -The sendable message
        '''
        # determine if user wants to send an email message or phone text
        send_to_phone = False
        if 'y' in input("Do you want to send an email message? (y/n): ").lower():
            msg = self.componse_email_msg(email_service_provider_info)
        else:
            msg = self.compose_text_msg(receiver_contact_info)

        return msg


    def compose_text_msg(self, receiver_contact_info):
        receiver_carrier = receiver_contact_info['carrier'].lower()        

        # Check if this email provider allows emails to be sent to phone numbers
        lower_case_list = list(map(lambda x:x.lower(), self.email_providers_info.keys()))
        # use index of lower case match to get actual value of key according to original mapped dict keys
        dict_keys_mapped_to_list = list(map(lambda x:x, self.email_providers_info.keys()))

        if receiver_carrier in lower_case_list:
            index_in_list_of_carrier = lower_case_list.index(receiver_carrier)
            key_for_desired_carrier = dict_keys_mapped_to_list[index_in_list_of_carrier]

            if 'special_address' not in self.email_providers_info[key_for_desired_carrier].keys():
                print("Sending text messages to {0} {1} is not possible due to their cell provider".format(
                                                    receiver_contact_info['first_name'], receiver_contact_info['last_name']))

                # Since cant send a text message to the person, ask if user want to send email message instead
                if input("Do you want to send an email instead (y/n): ").lower() == 'y':
                    return self.componse_email_msg()
                
                # If user cant send a text and wont send an email then just return
                else:
                    return None
            else:
                domain_name = self.email_providers_info[key_for_desired_carrier]['special_address']

        # Remove all non-numerical parts of phone number (should be contiguous 10 digit number)
        actual_phone_num = ''.join(char for char in receiver_contact_info['phone_num'] if char.isdigit())
        
        text_msg_address = "{0}@{1}".format(actual_phone_num, domain_name)
        print("Sending text message to {0}".format(text_msg_address))
        

        # Get content to send in text message
        body = "text msg body" # TODO take in input
        
        # setup the parameters of the message (dont need subject for text messages)
        msg = MIMEMultipart() # create a message object
        msg['From'] = self.my_email_address
        msg['To'] = text_msg_address
        # add in the message body
        msg.set_payload(body)
        # msg.attach(MIMEText(body, 'plain'))
        return msg



    def componse_email_msg(self, email_service_provider_info):
        # Get a list of all possible message types
        list_of_msg_types = [types.replace('.txt', '') for types in os.listdir(os.path.join(path_to_this_dir, 'message_templates'))]
        contents = ''
        
        type_of_msg = 'default' 
        path_to_msg_template = os.path.join(self.message_templates_dir, 'default.txt')

        with open(path_to_msg_template) as read_file:
            contents = read_file.read()

        for msg_type in list_of_msg_types:
            path_to_msg_template = os.path.join(self.message_templates_dir, msg_type + '.txt')
            with open(path_to_msg_template) as read_file:
                msg_contents = read_file.read()
            print("The {0} message type looks like: \n{1}".format(msg_type, msg_contents))
            if 'y' in input("Would you like to send this message type? (y/n): ").lower():
                type_of_msg = msg_type   
                contents = msg_contents 
                break


        # create the body of the email to send
        # read in the content of the text file to send as the body of the email

        # TODO create other elif statements for different cases
        if type_of_msg == "test_msg":
            receiver = str(receiver_contact_info['first_name'])
            sendable_msg = self.read_template(path_to_msg_template).substitute(receiver_name=receiver, sender_name=self.my_email_address) 

        elif type_of_msg == 'input_content':
            my_input = input("Input what you would like to send in the body of the email: ")
            sendable_msg = self.read_template(path_to_msg_template).substitute(content=my_input)
        
        # Default to default file 
        else:
            sendable_msg = contents

        print("Sending message:\n{0}".format(sendable_msg))

        # setup the parameters of the message
        msg = MIMEMultipart() # create a message object
        msg['From'] = self.my_email_address
        msg['To'] = receiver_contact_info['email'] # send message as if it were a text
        msg['Subject'] = "Emailing Application"
        # add in the message body
        msg.attach(MIMEText(sendable_msg, 'plain'))
        return msg


    def read_template(self, path_to_file):
        with open(path_to_file, 'r+', encoding='utf-8') as template_file:
            template_file_content = template_file.read()
        return Template(template_file_content)

    def get_receiver_contact_info(self, my_first_name, my_last_name):
        '''
            This function will search the existing database for entries with the input first_name and last_name.\n

            Returns:\n
                Dictionary of format: {first name, last name, email, carrier, phone number}
                The phone number return accepts common type of seperaters or none (ex: '-')             
        '''

        receiver_contact_info_dict = {}
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
                    receiver_contact_info_dict = self.contact_list[last_name][first_name]
                    email = receiver_contact_info_dict['email']
                    phone_num = receiver_contact_info_dict['phone_number']
                    carrier = receiver_contact_info_dict['carrier']

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

    def connect_to_email_server(self, host_address, port_num=465):
        '''
            This function is responsible for connecting to the email server.
            Args:
                - host_address: contains information about host address of email server 
                - port_num: contains infomraiton about the port # of email server (defaults to 465 for secure connections)
        '''
        # Get email login
        self.my_email_address = input("Enter your email address: ")
        password = getpass.getpass(prompt="Password for user {0}: ".format(self.my_email_address))

        server = host_address
        my_port_num = port_num

        # Establish connection to email server using self.my_email_address and password given by user
        print("Connecting to smtp email server")
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        
        self.email_server = smtplib.SMTP(host=server, port=int(my_port_num))
        self.email_server.ehlo()
        self.email_server.starttls(context=context)
        self.email_server.ehlo()        

        # Try to login to email server, if it fails then catch exception
        try:
            self.email_server.login(self.my_email_address, password)
        except Exception as error:
            if '535' in str(error):
                # Sometimes smtp servers wont allow connection becuase the apps trying to connect are not secure enough
                # TODO make connection more secure
                print("\nCould not connect to email server because of error:\n{0}\n".format(error))
                print("Try changing your account settings to allow less secure apps to allow connection to be made.")
                link_to_page = "https://security.google.com/settings/security/apppasswords?pli=1"
                print("Or try enabling two factor authorization and generating an app-password\n{0}".format(link_to_page))
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
        # receiver_contact_info contains first_name, last_name, email, carrier, phone number
        receiver_contact_info = email.get_receiver_contact_info('nick', 'rizzo')
    
    # If user gives input use those values
    else:
        if len(sys.argv) < 2: print("Invalid number of arguments entered!")
        else:
            # Get arguments from when script is called
            first_name = sys.argv[1]
            last_name = sys.argv[2]
            receiver_contact_info = email.get_receiver_contact_info(first_name, last_name)
    

    email.send_email(receiver_contact_info)


    


