import json
import os
import re
import sqlite3
import subprocess
import datetime
from b64img import icon64, close64, launch64, check64, girl64, background_image, exclaim64

import sys
import FreeSimpleGUI as sg


def locate_ww_path(starting_path):
    if os.path.isfile(starting_path):
        starting_path = os.path.dirname(starting_path)
    for dirpath in os.walk(starting_path):
        try_path = dirpath[0]
        print(try_path)
        if try_path.endswith('Wuthering Waves Game'):
            return try_path
        elif 'Wuthering Waves Game' in try_path:
            while not (try_path.endswith('Wuthering Waves Game')):
                try_path = os.path.abspath(os.path.join(try_path, '..'))
            return try_path
        elif 'Wuthering Waves' in try_path:
        	for fd in os.scandir(try_path):
        		if fd.name == "Wuthering Waves Game" and os.path.isdir(fd):
        			locate_ww_path(os.path.join(try_path, fd.name))


def set_starting_path():
    try:
        if str(gameDir).endswith("Wuthering Waves Game"):
            return gameDir
        else:
            starting_path = sg.popup_get_folder("Select 'Wuthering Waves Game' Folder (Hit Okay if you've used before)", history=True,history_setting_filename="wwpath")
            ww_path = locate_ww_path(starting_path)
            sg.user_settings_set_entry('wwpath', ww_path)
            return ww_path
    except Exception as e:
    	sg.popup(f"Issue getting path, error: {e}")


def tbutton(image_data, key, tooltip):
    button = sg.Button(font='Any 12', image_data=image_data, mouseover_colors=('white', None),
                       button_color=('black', sg.theme_background_color()), border_width=0, image_subsample=2,
                       pad=(0, 0), key=key, image_size=(64, 64), auto_size_button=True)
    text = sg.Text(tooltip, font='Any 10', size=(15, 1), justification='center', auto_size_text=True, )
    return sg.Column([[button], [text]], element_justification='c')


def check_patch(fPath):
    con = sqlite3.connect(fPath)
    cur = con.cursor()
    res = cur.execute(
            "SELECT json_extract(value, '$.KeyCustomFrameRate') as CustomFrameRate FROM LocalStorage WHERE key = 'GameQualitySetting'")
    regex = r"(\d+)"

    try:
        result = re.search(regex, str(res.fetchall()), )
        with open(os.path.join(os.path.dirname(sys.argv[0]),"log.txt"), "a") as log:
        	print(result.group(1), file=log)
        return result.group(1)
    except AttributeError:
        pass


def execute_patch(fPath):
    con = sqlite3.connect(fPath)
    cur = con.cursor()
    res = cur.execute(
            "UPDATE LocalStorage SET value = json_replace(value, '$.KeyCustomFrameRate', 360) WHERE key = 'GameQualitySetting'")
    res.fetchone()
    con.commit()
    con.close()


def patch_loop(dataDir):
    datadir = os.path.abspath(dataDir)
    i = 0
    for fileentry in os.scandir(dataDir):
        file_path = fileentry.path
        if file_path.endswith(".db"):
            dbnum = str(file_path).split('.db')[0][-1]
            with open(os.path.join(os.path.dirname(sys.argv[0]),"log.txt"), "a") as log:
            	print(file_path)
            	print(file_path, file=log)
            fps = str(check_patch(file_path))
            with open(os.path.join(os.path.dirname(sys.argv[0]),"log.txt"), "a") as log:
            	print(f"db{dbnum}: {fps}",file=log)
            execute_patch(file_path)
            patched = check_patch(file_path)
            while (patched == "[(60,)]" and i < 20):
                execute_patch(file_path)
                patched = check_patch(file_path)
                i += 1


def main():
    dataPath = "\\Client\\Saved\\LocalStorage\\"
    dataExt = ".db"
    procPath = "\\Client\\Binaries\\Win64\\Client-Win64-Shipping.exe"
    try:
        f_path = os.path.join(os.getcwd(), "wwUnlock.json")
        f = json.load(f_path)
        print(f)
        global gameDir
        gameDir = f['gameDir']
        print(gameDir)
        global gamePath
        gamePath = gameDir + '\\Client-Win64-Shipping,.exes'
        print(gamePath)
        filePath = f['filePath']
        print(filePath)
        global gameArgs
        gameArgs = f['gameArgs']
    except Exception as e:
        gameDir = ""
        filePath = ""
        gamePath = ""
        gameArgs = ""

    if not os.path.exists(str(f_path)) or gameDir == "":
        startingPath = os.path.abspath(str(set_starting_path()))
        gameDir = startingPath
        gamePath = os.path.abspath(str(gameDir) + str(procPath))
        filePath = os.path.abspath(str(gameDir) + str(dataPath))
        data = {
                "gameDir": gameDir,
                "gamePath": gamePath,
                "filePath": filePath,
                "gameArgs": gameArgs
        }
        with open(f_path, "w") as write_json:
            json.dump(data, write_json)


    toolbar_buttons = [[tbutton(launch64, '-LAUNCH-', 'Launch Game'),
                        tbutton(exclaim64, '-SETARGS-','Set Args'),
                        tbutton(check64, '-CHECKFPS-', 'Patch FPS'),
                        tbutton(close64, '-CLOSE-', 'Close Launcher')]]

    layout = [[sg.Col(toolbar_buttons, background_color='light grey')]]

    window = sg.Window('Wuthering Waves FPS Unlock', layout, auto_size_text=True, no_titlebar=True,
                       transparent_color='dark grey',
                       grab_anywhere=True, alpha_channel=100, margins=(4, 0), finalize=True, resizable=True)

    while True:
        button, value = window.read()
        if button == '-CLOSE-' or button is None:
            break
        elif button == '-SETARGS-':
            args = sg.popup_get_text(message="Enter the startup command as you would in cmd", default_text='d3d11', no_titlebar=True,
                                     grab_anywhere=True, keep_on_top=True, history=True)
            try:
                argslist = str(args)
                gameArgs = argslist
                with open(os.path.join(os.path.dirname(sys.argv[0]),"log.txt"), "a") as log:
                	print(gameArgs,file=log)
            except Exception as e:
            	with open(os.path.join(os.path.dirname(sys.argv[0]),"log.txt"), "a") as log:
                	print(e,file=log)
        elif button == '-LAUNCH-':
            gamestring = f"{gamePath} {gameArgs}"
            print(gamestring)
            subprocess.run(gamestring)
        elif button == '-CHECKFPS-':
            os.chdir(gameDir)
            dataPath = "Client\\Saved\\LocalStorage"
            datadir = os.path.abspath(dataPath)
            patch_loop(datadir)

    window.close()


try:
	today = str(datetime.datetime)
	with open(os.path.join(os.path.dirname(sys.argv[0]),"log.txt"),"a") as log:
		print(f"Starting patcher {datetime.datetime.now()}", file=log)
except FileNotFoundError:
	with open(os.path.join(os.path.dirname(sys.argv[0]),"log.txt"),"w") as log:
		print(f"{datetime.datetime} Starting patcher", file=log)
main()