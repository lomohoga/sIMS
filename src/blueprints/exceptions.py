# exception thrown for operations that refer to non-existent rows in database
class NoRowsError (Exception):
    def __init__ (self, message):
        self.args = (message,)

    def __str__ (self):
        return self.args[0]
    
# exception thrown when trying to update request status against correct status flow
class RequestStatusError (Exception):
    def __init__ (self, message):
        self.args = (message,)

    def __str__ (self):
        return self.args[0]
    
# exception thrown when trying to issue item that has already been issued
class ItemIssuedError (Exception):
    def __init__ (self, message):
        self.args = (message,)

    def __str__ (self):
        return self.args[0]