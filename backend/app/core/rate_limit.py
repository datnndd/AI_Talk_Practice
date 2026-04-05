from slowapi import Limiter
from slowapi.util import get_remote_address

# In-memory limiter for simple rate limiting.
# Can be configured to use Redis in production for distributed limits.
limiter = Limiter(key_func=get_remote_address)
