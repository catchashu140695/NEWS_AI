--Sadtalker Installation--
pip install torch==1.12.1+cu113 torchvision==0.13.1+cu113 torchaudio==0.12.1 --extra-index-url https://download.pytorch.org/whl/cu113
pip install ffmpeg


--Install Eel app--
pip install eel
pip install wxpython
pip install moviepy
pip install SpeechRecognition
pip install g4f
pip install curl_cffi
pip install gtts playsound
pip install pygame
pip install pydub
pip install newsapi-python


--Prepare exe--
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --add-data "web;web" app.py

