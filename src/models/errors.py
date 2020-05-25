class RoleNotFoundError(Exception):
    def __init__(self, arg1, arg2=None):
        self.arg1 = arg1
        self.arg2 = arg2
        super(RoleNotFoundError, self).__init__(arg1)
