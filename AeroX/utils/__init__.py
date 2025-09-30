from .config import *

from .Tools import *

from .paginators import *

from .paginator import *

from .tickets import get_ticket_channel ,get_ticket_role ,is_ticket_channel ,user_has_support_role ,validate_ticket_data 



from .giveaway_utils import *

try :
    from .giveaway_utils import *
except ImportError as e :
    print (f"[UTILS] Warning: Could not import giveaway_utils: {e}")
    pass 
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
