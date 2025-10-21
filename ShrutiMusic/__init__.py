from ShrutiMusic.core.bot import Nand
from ShrutiMusic.core.dir import dirr
from ShrutiMusic.core.git import git
from ShrutiMusic.core.userbot import Userbot
from ShrutiMusic.misc import dbb, heroku

from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = Nand()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
