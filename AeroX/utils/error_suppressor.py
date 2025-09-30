
def suppress_local_errors (func ):
    """Decorator to suppress local error handlers in favor of centralized error handling"""
    def wrapper (*args ,**kwargs ):
        try :
            return func (*args ,**kwargs )
        except Exception :

            pass 
    return wrapper 

class ErrorSuppressor :
    """Context manager to suppress local error messages"""
    def __init__ (self ):
        self .suppressed =False 

    def __enter__ (self ):
        self .suppressed =True 
        return self 

    def __exit__ (self ,exc_type ,exc_val ,exc_tb ):
        if exc_type is not None :

            return True 
        return False 

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
