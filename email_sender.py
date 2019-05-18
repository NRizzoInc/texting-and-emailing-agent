import os
import sys
import json
import smtplib
import email
import pprint

path_to_this_dir = os.path.dirname(os.path.abspath(__file__))

class email_sender():
    def __init__(self):

        self.path_to_contact_list = os.path.join(path_to_this_dir, "contacts.json")
        self.contact_list = self.load_json()
        print("The current contact list is:\n")
        pprint.pprint(self.contact_list)

    def send_email(self):
        pass


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
    


