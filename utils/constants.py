# URL API Configs
MAIN_URL = "https://animetosho.org/animes"
REMOVE_REPACK = "?filter%5B0%5D%5Bt%5D=nyaa_class&filter%5B0%5D%5Bv%5D=remake&order=date-a"
DEFAULT_TIMEOUT = 15
DEFAULT_ATTEMPTS = 3
DEFAULT_WAIT_TIME = 15.0

# Logger config
FORMAT = "[%(filename)s | %(funcName)s : %(lineno)s] %(levelname)s: %(message)s"

# REGEX configs
QUALITY_REGEX = r'(\d{3,4}p)'  # matches quality, e.g. 720p
SEQUENCE_REGEX = r'\[([A-Z0-9]{8})\]'  # matches torrent sequence

# PARSER configs
PREFERENCE_RAWS = ["[SubsPlease]", "[Erai-raws]"]
DESIRED_SUBS = "eng"
MEMBER_CUT = 20000
PATH_ID_MEMBER_MAP = "misc/mal_id_member_count.json"
