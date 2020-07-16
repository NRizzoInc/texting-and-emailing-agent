## Database Structure

* Both collections will be handled by seperate classes (which extend a base class for utility)
  * These collection classes are funneled and inhereted by a single master controller for ease of use
* The `users` collection will contain important login information for their email accounts
  * Each "card" in this collection will contain:
    * Serialized copy of their `User` object
      * Their `User` objects will be maintained across sessions
    * username
    * password
    * UUID
* The `contacts` collection will contain one card for each user within the `users` database (mapped by UUID)
  * Each card will contain a json of that user's contact list
