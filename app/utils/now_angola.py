from datetime import datetime
from zoneinfo import ZoneInfo

ANGOLA_TZ = ZoneInfo("Africa/Luanda")

def now_angola():
    return datetime.now(ANGOLA_TZ)
