
import threading
import eel
from LongVideos import ProjectMaster
from LongVideos import VideoDetails
from LongVideos import LongVideoProcess
from LongVideos import NewsShorts
from LongVideos import TalkingHead
from Utilities import db_Connection
from Utilities import util



eel.init('web')  # This is the folder where your HTML, JS, CSS files for the Eel app are stored

def start_eel():   
    eel.start('base.html', size=(1920, 1080))  # This opens the Eel window with the specified file

# Start Eel
start_eel()

