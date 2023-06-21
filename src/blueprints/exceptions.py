class DatabaseConnectionError (Exception):
    def __init__ (self, *args):
        super().__init__(*args)

    def __str__ (self):
        return "Could not connect to the database. Please make sure that the MySQL service is running, then try again."

### inventory errors ###

# exception for items not in database
class ItemNotFoundError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['item'],)

    def __str__ (self) -> str:
        return f"Item {self.args[0]} not found in database."
    
# exception for categories not in database
class CategoryNotFoundError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['category'],)

    def __str__ (self) -> str:
        return f"Category {self.args[0]} not found in database."

# exception thrown when trying to add item with already existing item ID
class ExistingItemError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['item'],)

    def __str__ (self):
        return f"Item {self.args[0]} already exists in the database."
    
# exception thrown when trying to add category with already existing name
class ExistingCategoryError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['category'],)

    def __str__ (self):
        return f"Category {self.args[0]} already exists in the database."

# exception thrown when trying to remove item that appears in an ongoing request
class OngoingRequestItemError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['item'], kwargs['requests'])

    def __str__ (self):
        return f"Cannot delete item {self.args[0]} because it is currently in {'an ongoing request' if self.args[1] == 1 else 'multiple ongoing requests'}."

### request errors ###

# exception for requests not in database
class RequestNotFoundError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['request'],)

    def __str__ (self) -> str:
        return f"Request #{self.args[0]} not found in database."
    
# exception thrown when trying to update request status against correct status flow
class RequestStatusError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['from_status'], kwargs['to_status'])

    def __str__ (self):
        if self.args == (1, 3): return "Cannot issue a pending request."
        if self.args == (1, 4): return "Cannot receive a pending request."

        if self.args == (2, 2): return "Request is already approved."
        if self.args == (2, 4): return "Cannot receive an unissued request."
        if self.args == (2, 5): return "Cannot deny an approved request."

        if self.args == (3, 2): return "Request is already approved."
        if self.args == (3, 3): return "Request has already been issued."
        if self.args == (3, 5): return "Cannot deny an issued request."

        if self.args == (4, 2): return "Request has already been completed."
        if self.args == (4, 3): return "Request has already been completed."
        if self.args == (4, 4): return "Request has already been completed."
        if self.args == (4, 5): return "Cannot deny a completed request."
        if self.args == (4, 6): return "Cannot cancel a completed request."

        if self.args == (5, 2): return "Cannot approve a denied request."
        if self.args == (5, 3): return "Cannot issue a denied request."
        if self.args == (5, 4): return "Cannot receive a denied request."
        if self.args == (5, 5): return "Request has already been denied."
        if self.args == (5, 6): return "Cannot cancel a denied request."

        if self.args == (6, 2): return "Cannot approve a cancelled request."
        if self.args == (6, 3): return "Cannot issue a cancelled request."
        if self.args == (6, 4): return "Cannot receive a cancelled request."
        if self.args == (6, 5): return "Cannot deny a cancelled request."
        if self.args == (6, 6): return "Request has already been cancelled."

# exception thrown when trying to issue items in a request that is not in the approved stage
class IllegalIssueError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['request'],)

    def __str__ (self):
        return f"Cannot issue items in request #{self.args[0]} since it is not at the approved stage."

# exception thrown when trying to issue a request with unissued items
class IncompleteIssueError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['request'],)

    def __str__ (self):
        return f"Cannot issue request #{self.args[0]} since some items in the request have not yet been issued."

# exception thrown when trying to issue item that has already been issued
class ItemIssuedError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['item'], kwargs['request'])

    def __str__ (self):
        return f"Item {self.args[0]} has already been issued in request #{self.args[1]}."

# exception thrown when item is not found in request
class ItemNotInRequestError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['item'], kwargs['request'])

    def __str__ (self):
        return f"Item {self.args[0]} is not in request #{self.args[1]}."

### user errors ###

# exception for users not in database
class UserNotFoundError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['username'],)

    def __str__ (self) -> str:
        return f"User {self.args[0]} was not found in the database."

# exception thrown when trying to perform actions with an account that was removed while performing said action
class SelfNotFoundError (UserNotFoundError):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__ (self):
        return "You may not perform this action since your account is no longer registered in the database."

# exception for emails not registered in database
class EmailNotFoundError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.args = (kwargs['email'],)

    def __str__ (self) -> str:
        return f"Email {self.args[0]} is not registered in the database."

# exception thrown when trying to promote custodians / demote personnel
class UserRoleError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['username'], kwargs['role'])

    def __str__ (self):
        if self.args[1] == 0: return "Cannot promote or demote the administrator."
        return f"Cannot {'demote' if self.args[1] == 2 else 'promote'} user {self.args[0]}; they are already {'personnel' if self.args[1] == 2 else 'a custodian'}."

# exception thrown when trying to perform actions with an account whose role was updated while performing said action
class SelfRoleError (UserRoleError):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__ (self):
        if self.args[1] == 1: return "You may not perform this action since your account was recently promoted to custodian."
        if self.args[1] == 2: return "You may not perform this action since your account was recently demoted to personnel."

# exception thrown when email is already registered
class ExistingEmailError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['email'],)

    def __str__ (self):
        return f"Email address {self.args[0]} has already been registered."

# exception thrown when email is invalid
class InvalidEmailError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['email'],)

    def __str__ (self):
        return f"Email {self.args[0]} is invalid. Please make sure the email is valid and that it is a Gmail address."
    
# exception thrown when password is incorrect
class IncorrectPasswordError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args = (kwargs['changing'],)

    def __str__ (self):
        if self.args[0]: "The password you have entered does not match your current password. Please try again."
        return "The password you have entered is incorrect. Please try again."

# exception thrown when password reset code has expire
class ExpiredCodeError (Exception):
    def __init__ (self, *args):
        super().__init__(*args)

    def __str__ ():
        return "The code entered is correct, but has expired."
    
# exception thrown when password reset code is incorrect
class IncorrectCodeError (Exception):
    def __init__ (self, *args):
        super().__init__(*args)

    def __str__ ():
        return "The code entered is incorrect."

### form generation errors ###

class FormGenerationError (Exception):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args)
        self.args(form = kwargs['form'])

    def __str__ (self):
        return f"Could not generate Appendix {self.args[0]}."
