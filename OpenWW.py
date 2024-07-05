import json,pprint,os,re,sqlite3,subprocess,datetime,sys
from b64img import icon64, close64, launch64, check64, girl64, background_image, exclaim64, wwmi64
import FreeSimpleGUI as sg
from pyinjector import inject

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
        elif sg.user_settings_get_entry('wwpath'):
            print(sg.user_settings_get_entry('wwpath'))
            return sg.user_settings_get_entry('wwpath')
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
            "UPDATE LocalStorage SET value = json_replace(value, '$.KeyCustomFrameRate', 120) WHERE key = 'GameQualitySetting'")
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

def init_fps_patch():
    os.chdir(gameDir)
    dataPath = "Client\\Saved\\LocalStorage"
    datadir = os.path.abspath(dataPath)
    patch_loop(datadir)

def has_plugins(path):
    try:
        for file in os.scandir(path):
            if os.path.exists(file):
                return True
        else:
            return False
    except Exception as e:
        print(e)
        print("no plugins")
        return False

def delete_streamline():
    os.chdir(gameDir)
    try:
        nvidiaPath = os.path.join(gameDir,
                                  "Engine\\Plugins\\Runtime\\Nvidia\\Streamline\\Binaries\\ThirdParty\\Win64")
        dlssPath = os.path.join(gameDir,
                                "Engine\\Plugins\\Runtime\\Nvidia\\DLSS\\Binaries\\ThirdParty\\Win64\\nvngx_dlss.dll")
        nvidiaPath2 = os.path.join(gameDir,
                                   "Engine\\Plugins\\Runtime\\Nvidia\\Streamline\\Binaries\\ThirdParty\\noload")
        if (has_plugins(nvidiaPath) or os.path.exists(dlssPath)):
            try:
                os.remove(dlssPath)
                os.rename(nvidiaPath, nvidiaPath2)
                if (has_plugins(nvidiaPath)):
                    for file in os.scandir(nvidiaPath):
                        os.remove(file)
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)


def patch_engine_ini():
    engine_ini = os.path.join(gameDir,"Client\\Saved\\Config\\WindowsNoEditor\\Engine.ini" )
    if os.path.exists(engine_ini):
        with open(engine_ini, "r+") as engine_file:
            engine_text = engine_file.read()
            print(engine_text)

            match = re.match(r"(LODDistanceScale=20)|(Textures=1)",engine_text, re.MULTILINE )
            try:
                if match:
                    return True
                else:
                    engine_text += "\n[ConsoleVariables]\nr.Kuro.SkeletalMesh.LODDistanceScale=20\nr.Streaming.FullyLoadUsedTextures=1"
                    print(engine_text)
                    engine_file.seek(0)
                    engine_file.write(engine_text)
                    return True
            except Exception as e:
                print(e)
                return False

def patch_d3dx():
    try:
        if wwmi_path:
            print(wwmi_path)
            d3dxini = os.path.join(wwmi_path, "d3dx.ini")
            print(d3dxini)

            with open(d3dxini, "r+") as d3dx_file:
                d3dx_txt = str(d3dx_file.read())
                d3dx_txt = re.sub(r"\nlaunch", r"\n;launch", d3dx_txt)
                d3d_txt = re.sub(r"load_library_redirect=1",r"load_library_redirect=2", d3dx_txt)
                d3d_txt = re.sub(r";proxy_d3d11 = d3d11_helix\.dll",r"proxy_d3d11=ReShade64\.dll", d3d_txt)
                d3dx_file.seek(0)
                d3dx_file.write(d3dx_txt)
                print(d3dx_txt)
                return True
    except Exception as e:
        print(e)
        return False

def init_wwmi_config():
    try:
        delete_streamline()
        #engine = patch_engine_ini()
        #print(engine)
    except Exception as e:
        print(e)
    try:
        f = json.load(configPath)
        wwmi_path = f['wwmi_path']
        if os.path.exists(wwmi_path):
            wwmi = True
            d3dx = patch_d3dx()
            return wwmi_path
    except Exception as e:
        print(e)
        wwmi_path = ""
    try:
        if not os.path.exists(wwmi_path):
            wwmi_path = sg.popup_get_folder("Pick wwmi install folder",
                                    history=True, history_setting_filename="wwmi_path")      
            sg.user_settings_set_entry('wwmi_path', wwmi_path)
            with open(configPath, "w") as f:
                data = {
                        "gameDir": gameDir,
                        "gamePath": gamePath,
                        "dbPath": dbPath,
                        "gameArgs": gameArgs,
                        "wwmi": True,
                        "wwmi_path": wwmi_path
                }
                json.dump(data, f)
            return wwmi_path
    except Exception as e:
        print(e)
        return ""



def main():
    global rtgi
    rtgi = False
    dataPath = "\\Client\\Saved\\LocalStorage\\"
    dataExt = ".db"
    procPath = "\\Client\\Binaries\\Win64\\Client-Win64-Shipping.exe"
    try:
        f_path = os.path.join(os.getcwd(), "wwUnlock.json")
        global configPath
        configPath = os.path.abspath(f_path)
        f = json.load(f_path)
        print(f)
        global gameDir
        gameDir = f['gameDir']
        print(gameDir)
        global gamePath
        gamePath = gameDir + '\\Client-Win64-Shipping.exe'
        print(gamePath)
        global dbPath
        dbPath = f['dbPath']
        print(dbPath)
        global gameArgs
        gameArgs = f['gameArgs']
        try:
            if os.path.exists(f['wwmi_path']):
                global wwmi_path
                wwmi_path = f['wwmi_path']
                global wwmi
                wwmi = f['wwmi']
        except Exception as e:
            print(e)
    except:
        gameDir = ""
        gamePath = ""
        dbPath = ""
        gameArgs = ""
        wwmi_path = ""
        wwmi = ""

    if not os.path.exists(str(f_path)) or gameDir == "":
        startingPath = os.path.abspath(str(set_starting_path()))
        gameDir = startingPath
        gamePath = os.path.abspath(str(gameDir) + str(procPath))
        dbPath = os.path.abspath(str(gameDir) + str(dataPath))
        gameArgs = ""
        data = {
                "gameDir": gameDir,
                "gamePath": gamePath,
                "dbPath": dbPath,
                "gameArgs": gameArgs,
                "wwmi": False,
                "wwmi_path": ""
        }
        with open(f_path, "w") as write_json:
            json.dump(data, write_json)


    toolbar_buttons = [[sg.T('❎', background_color=None, enable_events=True,justification='right', key='Exit')],
                        [tbutton(launch64, '-LAUNCH-', 'Launch Game'),tbutton(exclaim64, '-SETARGS-','Launch Options')],
                        [tbutton(check64, '-CHECKFPS-', 'Patch FPS'), tbutton(wwmi64, '-WWMI-', 'Configure WWMI')]]

    layout = [[sg.Col(toolbar_buttons, background_color='light grey')]]

    window = sg.Window('Wuthering Waves FPS Unlock', layout, auto_size_text=True, no_titlebar=True,
                       transparent_color='dark grey',
                       grab_anywhere=True, alpha_channel=100, margins=(4, 0), finalize=True, resizable=True)

    while True:
        button, value = window.read()
        if button is None:
            break
        elif button == '-SETARGS-':
            args = sg.popup_get_text(message="Enter any additional startup commands here. D3D11 is forced if using WWMI", default_text='-d3d11 -fileopenlog', no_titlebar=True,
                                     grab_anywhere=True, keep_on_top=True, history=True)
            try:
                argslist = str(args)
                if 'RTGI' in argslist:
                    argslist = argslist.split('RTGI')[0]
                    rtgi = True
                gameArgs = argslist
                with open(os.path.join(os.path.dirname(sys.argv[0]),"log.txt"), "a") as log:
                	print(gameArgs,file=log)
            except Exception as e:
            	with open(os.path.join(os.path.dirname(sys.argv[0]),"log.txt"), "a") as log:
                	print(e,file=log)
        elif button == '-LAUNCH-':
            print(wwmi)
            if os.path.exists(wwmi_path):
                print(wwmi_path)
                wwmi_exec = 'start "" "WWMI Loader.exe"'
                print(wwmi_exec)
                os.chdir(wwmi_path)
                os.system(wwmi_exec)
                ExecCmds=r' -ExecCmds="r.Kuro.SkeletalMesh.LODDistanceScale 20;r.Streaming.FullyLoadUsedTextures 1"'
                try:
                    if "-d3d11" not in gameArgs:
                        gameArgs += " -d3d11"
                    if ExecCmds not in gameArgs:
                        gameArgs += ExecCmds
                    print(gameArgs)
                except Exception as e:
                    with open(os.path.join(os.path.dirname(sys.argv[0]), "log.txt"), "a") as log:
                        print(e, file=log)
            os.chdir(gameDir)
            gamestring = f"{gamePath} {gameArgs}"
            print(gamestring)
            game = subprocess.run(gamestring)
            break
        elif button == '-WWMI-':
            wwmi_path = init_wwmi_config()
            print(wwmi_path)
        elif button == '-CHECKFPS-':
            init_fps_patch()
        if button == 'Exit':
            break
    window.close()



try:
	today = str(datetime.datetime)
	with open(os.path.join(os.path.dirname(sys.argv[0]),"log.txt"),"a") as log:
		print(f"Starting patcher {datetime.datetime.now()}", file=log)
except FileNotFoundError:
	with open(os.path.join(os.path.dirname(sys.argv[0]),"log.txt"),"w") as log:
		print(f"{datetime.datetime} Starting patcher", file=log)
main()