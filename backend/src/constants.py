"""
    @file: Purpose is to prevent magic numbers & burried constants by having a single point of truth
"""
class Constants():
    def __init__(self):
        super().__init__()

        # Databases
        self._dbName = "email-web-app"
        self._userCollectionName = "users"
        self._contactsCollectionName = "contacts"
        self._cliUserId = "localhost"

        # EmailAgent / Databases
        self.contactListKey = "contact-list"