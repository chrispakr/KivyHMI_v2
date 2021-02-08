from kivy.app import App
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition, NoTransition
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty, StringProperty, ColorProperty, \
    ListProperty, AliasProperty
from kivy.animation import Animation
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.utils import get_color_from_hex
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.label import Label
import kivy.utils
from kivy.uix.image import Image
from kivy.core.image import Image as CoreImage
import os
from sys import platform
import paho.mqtt.client as mqtt
from configparser import ConfigParser
from enum import Enum
import sys
import json

from telnetlib import Telnet
import getpass

from opcua import Client
from opcua import ua

from threading import Thread
import threading

from ping3 import ping
import pyads

#python_list = json.loads(json_data)
os.environ["KIVY_IMAGE"] = "pil"

enablePlcCommunication = False

cp_VisionSensor = ConfigParser()
cp_Mqtt = ConfigParser()

cp_VisionSensor.read("settings/config_visionsensor.ini")
visionSensorConnectionData = cp_VisionSensor["VisionSensor"]
# client = Client("opc.tcp://" + visionSensorConnectionData["ip_address"] + ":4840")

tn_HOST = visionSensorConnectionData["ip_address"]
tn_user = visionSensorConnectionData["username"]
tn_password = visionSensorConnectionData["password"]
tn_timeout = int(visionSensorConnectionData["timeout"])

cp_Mqtt.read("settings/config_mqtt.ini")
mqtt_configData = cp_Mqtt["mqtt"]

# Window.show_cursor = False
mqtt_ServerIp = mqtt_configData["ip_address"]

sTopic_getPlcIsOnline = mqtt_configData["sTopic_getPlcIsOnline"]

sTopic_setLedColor = mqtt_configData["sTopic_setLedColor"]
sTopic_getLedColor = mqtt_configData["sTopic_getLedColor"]
sTopic_setLedBrightnessWhite = mqtt_configData["sTopic_setLedBrightnessWhite"]
sTopic_setLedBrightnessRed = mqtt_configData["sTopic_setLedBrightnessRed"]
sTopic_setLedBrightnessGreen = mqtt_configData["sTopic_setLedBrightnessGreen"]
sTopic_setLedBrightnessBlue = mqtt_configData["sTopic_setLedBrightnessBlue"]
sTopic_getLedBrightnessWhite = mqtt_configData["sTopic_getLedBrightnessWhite"]
sTopic_getLedBrightnessRed = mqtt_configData["sTopic_getLedBrightnessRed"]
sTopic_getLedBrightnessGreen = mqtt_configData["sTopic_getLedBrightnessGreen"]
sTopic_getLedBrightnessBlue = mqtt_configData["sTopic_getLedBrightnessBlue"]

sTopic_initDh = mqtt_configData["sTopic_initDh"]
sTopic_setDhPosition = mqtt_configData["sTopic_setDhPosition"]
sTopic_getDhPosition = mqtt_configData["sTopic_getDhPosition"]

sTopic_setMoveCommand = mqtt_configData["sTopic_setMoveCommand"]
sTopic_getMoveCommand = mqtt_configData["sTopic_getMoveCommand"]
sTopic_curFilmMoveDirection = mqtt_configData["sTopic_curFilmMoveDirection"]
sTopic_curFilmSpeed = mqtt_configData["sTopic_curFilmSpeed"]

sTopic_getIsLightTableClosed = mqtt_configData["sTopic_getIsLightTableClosed"]
sTopic_frontSpoolDiameter = mqtt_configData["sTopic_frontSpoolDiameter"]
sTopic_rearSpoolDiameter = mqtt_configData["sTopic_rearSpoolDiameter"]

sTopic_fmc_State = mqtt_configData["sTopic_fmc_State"]
sTopic_startFilmInit = mqtt_configData["sTopic_startFilmInit"]
sTopic_startLoadFilm = mqtt_configData["sTopic_startLoadFilm"]
sTopic_stopLoadFilm = mqtt_configData["sTopic_stopLoadFilm"]
sTopic_filmLoadFastForward = mqtt_configData["sTopic_filmLoadFastForward"]
sTopic_enableFreeRun = mqtt_configData["sTopic_enableFreeRun"]
sTopic_disableFreeRun = mqtt_configData["sTopic_disableFreeRun"]

sTopic_availableJobs = mqtt_configData["sTopic_availableJobs"]
sTopic_setVsJobId = mqtt_configData["sTopic_setVsJobId"]
sTopic_curVsJobId = mqtt_configData["sTopic_curVsJobId"]
sTopic_getCurJobName = mqtt_configData["sTopic_getCurJobName"]


sBaseColor = get_color_from_hex("#2699fb")
sBaseGreyDark = get_color_from_hex("#464646")
sBaseGreyLight = get_color_from_hex("#A4A4A4")
sBaseWhite = get_color_from_hex("#FFFFFF")
sBaseBlack = get_color_from_hex("#000000")
# sBaseColor = get_color_from_hex("#FF4B09")

currentLedColor = 0
currentDhPosition = ""


def load_job_from_id(job_id):
    print("VS: start Load Job by ID")
    t_job_id = str(job_id)
    try:
        tn = Telnet(tn_HOST, 23, tn_timeout)
        # Login to Sensor
        print("Telnet connected")
        tn.read_until(b"User: ")
        tn.write(tn_user.encode('ascii') + b"\r\n")
        tn.read_until((b"Password: "))
        tn.write(b"\r\n")
        tn.read_until(b"User Logged In\r\n")
        # Login Finished
        tn.write(b"SJ" + t_job_id.encode('ascii') + b"\r\n")
        # print("set Job: " + t_job_id)
        call_ok = str(tn.read_until(b"\r\n"), 'utf-8')
        call_ok = call_ok.replace("\r\n", "")
        # print("callOK: " + call_ok)
        # return call_ok
        return call_ok
        tn.close()
    except IOError:
        print("error while connecting to vision-sensor")
        return -5, 0


def get_loaded_job_id():
    cur_jobId = 0
    try:
        tn = Telnet(tn_HOST, 23, tn_timeout)
        # Login to Sensor
        # print("Telnet connected")
        tn.read_until(b"User: ")
        tn.write(tn_user.encode('ascii') + b"\r\n")
        tn.read_until((b"Password: "))
        tn.write(b"\r\n")
        tn.read_until(b"User Logged In\r\n")
        # Login Finished
        tn.write(b"GJ" + b"\r\n")
        call_ok = str(tn.read_until(b"\r\n"), 'utf-8')
        call_ok = call_ok.replace("\r\n", "")
        # print("callOK: " + call_ok)
        if call_ok == "1":
            cur_jobId = str(tn.read_until(b"\r\n"), 'utf-8')
            cur_jobId = cur_jobId.replace("\r\n", "")
            # print("current loaded jobId: " + cur_jobId)
        else:
            cur_jobId = 0
        return call_ok, cur_jobId
        tn.close()
    except IOError:
        print("error while connecting to vision-sensor")
        return -5, 0


def read_job_information(job_id):
    t_job_id = str(job_id)
    try:
        tn = Telnet(tn_HOST, 23, tn_timeout)
        # Login to Sensor
        # print("Telnet connected")
        tn.read_until(b"User: ")
        tn.write(tn_user.encode('ascii') + b"\r\n")
        tn.read_until((b"Password: "))
        tn.write(b"\r\n")
        tn.read_until(b"User Logged In\r\n")
        # Login Finished
        tn.write(b"RJ" + t_job_id.encode('ascii') + b"\r\n")
        # print("get infos from Job" + t_job_id)
        call_ok = str(tn.read_until(b"\r\n"), 'utf-8')
        call_ok = call_ok.replace("\r\n", "")
        # print("callOK: " + call_ok)
        if call_ok == "1":
            filename = str(tn.read_until(b"\r\n"), 'utf-8')
            filename = filename.replace("\r\n", "")
            filename = filename.replace(".job", "")
            filename = filename.replace("_", " ")
            file_data = filename.split("-")
            # print("filename: " + filename)
            job_size = str(tn.read_until(b"\r\n"), 'utf-8')
            job_size = job_size.replace("\r\n", "")
            # print("jobSize: " + job_size)
        else:
            file_data = ""
        return call_ok, file_data
        tn.close()
    except IOError:
        print("error while connecting to vision-sensor")
        return -5, None


def set_vision_sensor_online_state(value):
    tValue = str(value)
    try:
        tn = Telnet(tn_HOST, 23, tn_timeout)
        # Login to Sensor
        # print("Telnet connected")
        tn.read_until(b"User: ")
        tn.write(tn_user.encode('ascii') + b"\r\n")
        tn.read_until((b"Password: "))
        tn.write(b"\r\n")
        tn.read_until(b"User Logged In\r\n")
        # Login Finished
        tn.write(b"SO" + tValue.encode('ascii') + b"\r\n")
        # print("set sensor_state to: " + tValue)
        call_ok = str(tn.read_until(b"\r\n"), 'utf-8')
        call_ok = call_ok.replace("\r\n", "")
        # print("callOK: " + call_ok)
        if call_ok == "1":
            if value == 0:
                App.get_running_app().vs_is_online = False
            if value == 1:
                App.get_running_app().vs_is_online = True
        return call_ok
        tn.close()
    except IOError:
        print("error while connecting to vision-sensor")
        return -5, None


def vs_read_current_job_information():
    _cur_job_id = get_loaded_job_id()
    if _cur_job_id[0] == "1":
        print("vs current jobId: " + _cur_job_id[1])
        App.get_running_app().vs_cur_job_id = _cur_job_id[1]
        cur_job_data = read_job_information(_cur_job_id[1])
        if int(_cur_job_id[1]) < 200:
            App.get_running_app().vs_cur_film_name = cur_job_data[1][1] + " - " + cur_job_data[1][2] + " / NEG"
        else:
            App.get_running_app().vs_cur_film_name = cur_job_data[1][1] + " - " + cur_job_data[1][2] + " / POS"
    else:
        App.get_running_app().vs_cur_film_name = "NO VISION SENSOR FOUND"


def vs_load_program(job_id):
    set_vision_sensor_online_state(0)
    load_job_from_id(job_id)
    vs_read_current_job_information()
    set_vision_sensor_online_state(1)
    App.get_running_app().vs_load_preset_state = 5


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(sTopic_getPlcIsOnline)
    client.subscribe(sTopic_getLedColor)
    client.subscribe(sTopic_getLedBrightnessWhite)
    client.subscribe(sTopic_getLedBrightnessRed)
    client.subscribe(sTopic_getLedBrightnessGreen)
    client.subscribe(sTopic_getLedBrightnessBlue)
    client.subscribe(sTopic_getDhPosition)
    client.subscribe(sTopic_getMoveCommand)
    client.subscribe(sTopic_getIsLightTableClosed)
    client.subscribe(sTopic_frontSpoolDiameter)
    client.subscribe(sTopic_rearSpoolDiameter)
    client.subscribe(sTopic_fmc_State)
    client.subscribe(sTopic_curFilmMoveDirection)
    client.subscribe(sTopic_curFilmSpeed)
    client.subscribe(sTopic_setVsJobId)
    client.publish(sTopic_setDhPosition, "Up")
    client.publish(sTopic_setLedColor, "Off")
    # App.get_running_app().connStatus = 1


def on_message(client, userdata, msg):
    global currentDhPosition
    cur_message = msg.payload.decode("utf-8").lower()
    # print (msg.topic + " // " + curMessage)

    if msg.topic == sTopic_getPlcIsOnline:
        if cur_message == "true":
            App.get_running_app().connStatus = 2

    if msg.topic == sTopic_getLedColor:
        if cur_message == "off":
            App.get_running_app().curLedColor = 0
        if cur_message == "white":
            App.get_running_app().curLedColor = 1
        if cur_message == "red":
            App.get_running_app().curLedColor = 2
        if cur_message == "green":
            App.get_running_app().curLedColor = 3
        if cur_message == "blue":
            App.get_running_app().curLedColor = 4

    if msg.topic == sTopic_getDhPosition:
        if cur_message == "up":
            App.get_running_app().curDhPosition = True
            # App.get_running_app().btnDhState = "normal"
            # print("/////incomingMessage // dhpos: UP")
        else:
            App.get_running_app().curDhPosition = False
            # App.get_running_app().btnDhState = "down"
            # print("/////incomingMessage // dhpos: DOWN")

    if msg.topic == sTopic_getMoveCommand:
        t_cur_message = int(cur_message)
        if t_cur_message == 0:
            print("set_btnFilmControl to False")
            App.get_running_app().disable_btnFilmControl = False
            App.get_running_app().disable_btnFilmMoveForward = False
            App.get_running_app().disable_btnFilmMoveBackward = False
            MainApp.filmInitIsFinished = False
            # ScreenInitFilm.stop_init_film()

        if t_cur_message == 60:
            MainApp.filmInitIsFinished = False
            # ScreenInitFilm.start_init_film()

        App.get_running_app().curMoveCommand = t_cur_message

    if msg.topic == sTopic_getIsLightTableClosed:
        pass
    if msg.topic == sTopic_frontSpoolDiameter:
        print(cur_message)
        App.get_running_app().spoolDiameterFront = int(cur_message)
    if msg.topic == sTopic_rearSpoolDiameter:
        App.get_running_app().spoolDiameterRear = int(cur_message)
    if msg.topic == sTopic_fmc_State:
        print("Current FilmMoveControllerStatus: " + cur_message)
        App.get_running_app().fmc_State = int(cur_message)
    if msg.topic == sTopic_getLedBrightnessWhite:
        print("Current ledBrightnessWhite: " + cur_message)
        App.get_running_app().ledBrightnessWhite = int(cur_message)
    if msg.topic == sTopic_getLedBrightnessRed:
        print("Current ledBrightnessRed: " + cur_message)
        App.get_running_app().ledBrightnessRed = int(cur_message)
    if msg.topic == sTopic_getLedBrightnessGreen:
        print("Current ledBrightnessGreen: " + cur_message)
        App.get_running_app().ledBrightnessGreen = int(cur_message)
    if msg.topic == sTopic_getLedBrightnessBlue:
        print("Current ledBrightnessBlue: " + cur_message)
        App.get_running_app().ledBrightnessBlue = int(cur_message)
    if msg.topic == sTopic_curFilmMoveDirection:
        print("current filmMoveDirection: " + cur_message)
        App.get_running_app().curFilmMoveDirection = int(cur_message)
    if msg.topic == sTopic_curFilmSpeed:
        print("current filmSpeed: " + cur_message)
        App.get_running_app().curFilmSpeed = int(cur_message)
    if msg.topic == sTopic_setVsJobId:
        print("mqtt: load VisionSensor-Preset: " + cur_message)
        App.get_running_app().vs_set_job_id = int(cur_message)


client_mqtt = mqtt.Client()
client_mqtt.on_connect = on_connect
client_mqtt.on_message = on_message
client_mqtt.connect_async(mqtt_ServerIp, 1883, 60)
client_mqtt.loop_start()

# LabelBase.register(name="StdFont", fn_regular="fonts/GalanoGrotesqueLight.otf")
LabelBase.register(name="StdFont", fn_regular="fonts/GalanoGrotesqueMedium.otf")
LabelBase.register(name="StdFontBold", fn_regular="fonts/GalanoGrotesqueMedium.otf")

Window.size = (800, 480)
Window.clearcolor = (0, 0, 0, 1)

if enablePlcCommunication:
    if platform == "linux" or platform == "linux2":
        pyads.add_route("5.71.85.220.1.1", "192.168.0.10")

    plc = pyads.Connection('5.71.85.220.1.1', 851, "192.168.0.10")
    plc.open()

    print(plc.read_by_name("MAIN.curFilmPosition", pyads.PLCTYPE_INT))
    print(plc.read_state())
    # plc.write_control(pyads.ADSSTATE_RUN, plc.read_state()[0], 0, pyads.PLCTYPE_INT)


class RestartPopup(FloatLayout):
    pass


def show_restartPopup():
    show = RestartPopup()
    popup_window = Popup(title="Warning - Please Confirm", content=show, size_hint=(None, None), size=(400, 200))
    popup_window.open()


def restart():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)


def program_close_handler():
    if client_mqtt.is_connected():
        client_mqtt.disconnect()


class FullScreenManager(ScreenManager):
    def __init__(self, **kwargs):
        super(FullScreenManager, self).__init__(**kwargs)
        self.add_widget(FullScreenInitHmi(name='fullScreenInitHmi'))
        self.add_widget(FullScreenHmiMenu(name='fullScreenHmiMenu'))


class SmMainScreen(ScreenManager):
    def __init__(self, **kwargs):
        super(SmMainScreen, self).__init__(**kwargs)
        self.add_widget(FilmTransportControl(name='screenFilmTransport'))
        self.add_widget(CameraControl(name="screenCameraControl"))
        self.add_widget(ProjectControl(name="screenProjectControl"))
        self.add_widget(ScreenSettings(name="screenSettings"))


class SmFilmMoveCenter(ScreenManager):
    def __init__(self, **kwargs):
        super(SmFilmMoveCenter, self).__init__(**kwargs)
        self.add_widget(ScreenFilmAnimation(name='screenFilmAnimation'))
        self.add_widget(ScreenLoadFilmAnimation(name="screenLoadFilmAnimation"))
        self.add_widget(ScreenSelectLedColor(name="screenSelectLedColor"))
        self.add_widget(ScreenSelectCameraType(name="screenSelectCameraType"))


class SmFilmMoveBottom(ScreenManager):
    def __init__(self, **kwargs):
        super(SmFilmMoveBottom, self).__init__(**kwargs)
        self.add_widget(ScreenButtonsFilmIsInsert(name='screenButtonsFilmIsInsert'))
        self.add_widget(ScreenButtonsNoFilmInsert(name="screenButtonsNoFilmInsert"))
        self.add_widget(ScreenButtonsLoadFilm(name="screenButtonsLoadFilm"))
        self.add_widget(ScreenInitFilm(name="screenInitFilm"))
        self.add_widget(ScreenButtonsSelectCameraType(name="screenButtonsSelectCameraType"))
        self.add_widget(ScreenSetVisionSensorSettings(name="screenSetVisionSensorSettings"))
        self.add_widget(ScreenEnableFreeRun(name="screenEnableFreeRun"))
        self.add_widget(ScreenFreeRunEnabled(name="screenFreeRunEnabled"))


class BaseScreen(Screen):
    pass


class FullScreenInitHmi(Screen):
    pass


class FullScreenHmiMenu(Screen):
    pass


class FilmTransportControl(Screen):
    pass


class CameraControl(Screen):
    pass


class ProjectControl(Screen):
    pass


class ScreenSettings(Screen):
    pass


class ScreenFilmAnimation(Screen):
    pass


class ScreenLoadFilmAnimation(Screen):
    pass


class ScreenSelectLedColor(Screen):
    pass


class ScreenButtonsFilmIsInsert(Screen):
    pass


class ScreenButtonsNoFilmInsert(Screen):
    pass


class ScreenButtonsLoadFilm(Screen):
    pass


class ScreenInitFilm(Screen):
    pass


class ScreenButtonsSelectCameraType(Screen):
    pass


class ScreenSetVisionSensorSettings(Screen):
    pass


class ScreenSelectCameraType(Screen):
    update = BooleanProperty(False)

    def on_update(self, *kwargs):
        if self.update:
            print("Update VS-Preset-List")
            self.ids.rvSelectCameraType.data = []
            fill_up_items = 12 - len(MainApp.vs_presets)
            for i in MainApp.vs_presets:
                self.ids.rvSelectCameraType.data.append({"text": i[1] + "\n" + i[2], "presetId": i[0]})
            for i in range(fill_up_items):
                self.ids.rvSelectCameraType.data.append({"text": "", "presetId": 0})
            self.ids.rvSelectCameraType.refresh_from_data()


class ScreenEnableFreeRun(Screen):
    pass


class SelectCameraButton(ToggleButton):
    def on_press(self):
        print(self.presetId)
        MainApp.vs_ui_selected_film_id = self.presetId


class DhButton(Button):
    curDhPosition = BooleanProperty()

    def on_curDhPosition(self, *kwargs):
        if not self.curDhPosition:
            dh_btn_animation = Animation(arrowAngle=180, duration=0.2)
            dh_btn_animation.start(self)
        if self.curDhPosition:
            dh_btn_animation = Animation(arrowAngle=0, duration=0.2)
            dh_btn_animation.start(self)


# class MoveFilmButton(Button):
#     def on_disabled(self, *kwargs):
#         if self.disabled == False:
#             btn_animation = Animation(background_color=sBaseColor, duration=0.2)
#             btn_animation.start(self)
#         else:
#             btn_animation = Animation(background_color=sBaseGreyDark, duration=0.2)
#             btn_animation.start(self)

class DownHolder(RelativeLayout):
    curDhPosition = BooleanProperty()

    def on_curDhPosition(self, *kwargs):
        if not self.curDhPosition:
            dh_ani = Animation(setPosition=0, duration=0.2)
            dh_ani.start(self)
        if self.curDhPosition:
            dh_ani = Animation(setPosition=15, duration=0.2)
            dh_ani.start(self)


class NavButton(Button):

    def on_disabled(self, *kwargs):
        if self.disabled:
            # print("startButonAni // True")
            btn_ani = Animation(alpha=0.2, duration=0.3)
            btn_ani.start(self)
        if not self.disabled:
            # print("startButonAni // False")
            btn_ani = Animation(alpha=1.0, duration=0.3)
            btn_ani.start(self)

    def disabled_change(self):
        print("EnableChanged")
        if self.disabled:
            self.alpha = 0.2
        else:
            self.alpha = 1.0


class SelectFilmInitMethod(Screen):
    pass


class ScreenLoadFilm(Screen):
    pass


class ScreenFreeRunEnabled(Screen):
    pass


class IpCheckSwitch(threading.Thread):
    def __init__(self, ip):
        threading.Thread.__init__(self)
        self.ip = ip

    def run(self):
        ping_result = ping(self.ip, timeout=1)

        if ping_result is None:
            print("EthernetSwitch offline...")
            App.get_running_app().switchConnected = False
        else:
            print("EthernetSwitch online...")
            App.get_running_app().switchConnected = True


class IpCheckVisionSensor(threading.Thread):
    def __init__(self, ip):
        threading.Thread.__init__(self)
        self.ip = ip

    def run(self):
        ping_result = ping(self.ip, timeout=1)

        if ping_result is None:
            print("VisionSensor offline...")
            App.get_running_app().visionSensorConnected = False
        else:
            print("VisionSensor online...")
            App.get_running_app().visionSensorConnected = True


class IpCheckFilmMoveController(threading.Thread):
    def __init__(self, ip):
        threading.Thread.__init__(self)
        self.ip = ip

    def run(self):
        ping_result = ping(self.ip, timeout=1)

        if ping_result is None:
            print("FilmMoveController offline...")
            App.get_running_app().filmMoveControllerConnected = False
        else:
            print("FilmMoveController online...")
            App.get_running_app().filmMoveControllerConnected = True


class IpCheckMainController(threading.Thread):
    def __init__(self, ip):
        threading.Thread.__init__(self)
        self.ip = ip

    def run(self):
        ping_result = ping(self.ip, timeout=1)

        if ping_result is None:
            print("MainController offline...")
            App.get_running_app().mainControllerConnected = False
        else:
            print("MainController online...")
            App.get_running_app().mainControllerConnected = True


class MainMenuBox(RelativeLayout):
    def on_rectPos_change(self):
        print("startMenuAnimation")
        btn_ani = Animation(alpha=0.2, duration=0.3)
        btn_ani.start(self)


class InfoTextPulseLabel(Label):
    border_color = ColorProperty()

    def __init__(self, **kwargs):
        super(InfoTextPulseLabel, self).__init__(**kwargs)
        self.border_color = sBaseGreyDark
        self.color = sBaseGreyDark
        Clock.schedule_interval(self.borderAnimation, 2)

    def borderAnimation(self, dtx):
        ani_border_glow = Animation(border_color=sBaseColor, color=sBaseWhite, t='in_out_quart', duration=1)
        ani_border_glow += Animation(border_color=sBaseGreyDark, color=sBaseGreyDark, t='in_out_expo', duration=0.5)
        ani_border_glow.start(self)


class MainApp(App):
    curDhPosition = BooleanProperty()
    btnDhArrowAngle = NumericProperty()
    dhButtonText = StringProperty()

    epo_state = BooleanProperty(False)

    connStatus = NumericProperty(1)
    spoolDiameterFront = NumericProperty(0)
    spoolDiameterRear = NumericProperty(0)
    curMoveCommand = NumericProperty(0)
    curFilmMoveDirection = NumericProperty(0)
    curFilmSpeed = NumericProperty(0)
    alpha_btnFilmMoveBackward = NumericProperty(1.0)
    alpha_btnFilmMoveForward = NumericProperty(1.0)
    alpha_btnFilmControl = NumericProperty(0.7)
    disable_btnFilmMoveBackward = BooleanProperty(False)
    disable_btnFilmMoveForward = BooleanProperty(False)
    disable_btnFilmControl = BooleanProperty(False)
    disable_btnStop = BooleanProperty(False)
    disable_btnFreeRun = BooleanProperty(False)

    visionSensor_LoadedPreset = NumericProperty(0)  # 0= Negativ / 1 = Positiv
    visionSensorConnected = BooleanProperty(False)
    mainControllerConnected = BooleanProperty(False)
    filmMoveControllerConnected = BooleanProperty(False)
    switchConnected = BooleanProperty(False)
    initHmiDisplayFinished = BooleanProperty(False)
    fmc_State = NumericProperty(0);
    freeRunEnabled = BooleanProperty(False)
    btnFreeRunText = StringProperty("Unlock Motors")
    arcSpoolFront = NumericProperty(0)
    arcSpoolRear = NumericProperty(0)

    # UI Colors
    baseColor = ColorProperty(sBaseColor)
    baseGreyDark = ColorProperty(sBaseGreyDark)
    baseGreyLight = ColorProperty(sBaseGreyLight)
    baseWhite = ColorProperty(sBaseWhite)
    baseBlack = ColorProperty(sBaseBlack)

    arcColorSpoolFront = StringProperty("#ff0000")
    arcColorSpoolRear = StringProperty("#ff0000")

    ledColorWhite = ColorProperty("#FFFFFF")
    ledColorRed = ColorProperty("#FF0000")
    ledColorGreen = ColorProperty("#00FF00")
    ledColorBlue = ColorProperty("#3699FB")

    # Global Light Variables
    curLedColor = NumericProperty(0)
    ledBrightnessWhite = NumericProperty(0)
    ledBrightnessRed = NumericProperty(0)
    ledBrightnessGreen = NumericProperty(0)
    ledBrightnessBlue = NumericProperty(0)
    get_ledBrightnessSlider = NumericProperty(0)
    set_ledBrightnessSlider = NumericProperty(0)

    mainMenuRectPosition = NumericProperty(360)

    initHmiAnimationPicPos = 100
    initHmiAnimationBottomPath = "pictures/animations/intro_Globe/"
    initHmiAnimationTopPath = "pictures/animations/intro_Line/"
    initHmiAnimationBottomImgSource = StringProperty(initHmiAnimationBottomPath + "100.png")
    initHmiAnimationTopImgSource = StringProperty(initHmiAnimationTopPath + "100.png")

    filmLoadAnimationPicPos = 100
    filmLoadAnimationBottomPath = "pictures/animations/filmLoading_Rolls/"
    filmLoadAnimationTopPath = "pictures/animations/filmLoading_Film/"
    filmLoadAnimationBottomImgSource = StringProperty(filmLoadAnimationBottomPath + "100.png")
    filmLoadAnimationTopImgSource = StringProperty(filmLoadAnimationTopPath + "100.png")

    filmMoveAnimationPicPos = 100
    filmMoveAnimationBottomPath = "pictures/animations/filmMove_Rolls/"
    filmMoveAnimationTopPath = "pictures/animations/filmMove_Film/"
    filmMoveAnimationBottomImgSource = StringProperty(filmMoveAnimationBottomPath + "100.png")
    filmMoveAnimationTopImgSource = StringProperty(filmMoveAnimationTopPath + "100.png")
    filmAnimationDelay = 1 / 25

    lastScreenIndex = 0
    curFilmTransportCenterScreen = StringProperty("screenFilmAnimation")
    curFilmTransportBottomScreen = StringProperty("screenButtonsNoFilmInsert")
    curFullScreen = StringProperty("fullScreenInitHmi")
    curMainScreen = StringProperty("screenFilmTransport")

    vs_ui_selected_film_id = NumericProperty(0)
    vs_ui_selected_film_type = NumericProperty(0)

    vs_presets = []
    # vs_selected_preset_temp = 0
    # vs_selected_preset = NumericProperty(0)
    vs_set_job_id = NumericProperty(0)
    vs_cur_job_id = NumericProperty(0)
    vs_cur_film_name = StringProperty("")
    vs_load_preset_state = NumericProperty(0)
    vs_is_online = BooleanProperty(False)
    updateList = BooleanProperty(False)

    def on_selectedCameraType(self, instance, value):
        print("cameraType changed to: " + str(self.selectedCameraType))

    def on_curLedColor(self, instance, value):
        print("led_color changed to: " + str(self.curLedColor))

    def on_fmc_State(self, instance, value):
        print("fmc-State changed to: " + str(self.fmc_State))

        if self.fmc_State == 0:
            SmFilmMoveCenter.transition = NoTransition()
            self.curFilmTransportCenterScreen = "screenFilmAnimation"
            SmFilmMoveBottom.transition = SlideTransition(direction="right")
            self.curFilmTransportBottomScreen = "screenButtonsNoFilmInsert"
            self.filmAnimationDirection = 0
            self.disable_btnFilmControl = True
            self.disable_btnFilmMoveBackward = True
            self.disable_btnFilmMoveForward = True
            self.disable_btnFreeRun = False
            self.disable_btnStop = True

        if self.fmc_State == 1:
            SmFilmMoveCenter.transition = NoTransition()
            self.curFilmTransportCenterScreen = "screenFilmAnimation"
            SmFilmMoveBottom.transition = SlideTransition(direction="left")
            self.curFilmTransportBottomScreen = "screenFreeRunEnabled"
            self.disable_btnFilmControl = True
            self.disable_btnFilmMoveBackward = True
            self.disable_btnFilmMoveForward = True
            self.disable_btnStop = True
            self.disable_btnFreeRun = False

        if self.fmc_State == 2:
            self.disable_btnFilmControl = True
            self.disable_btnFilmMoveBackward = False
            self.disable_btnFilmMoveForward = False
            self.disable_btnStop = True
            self.disable_btnFreeRun = False

        if self.fmc_State == 3:
            self.disable_btnFilmControl = True
            self.disable_btnFilmMoveBackward = False
            self.disable_btnFilmMoveForward = False
            self.disable_btnStop = True
            self.disable_btnFreeRun = False

        if self.fmc_State == 4:
            SmFilmMoveCenter.transition = NoTransition()
            self.curFilmTransportCenterScreen = "screenLoadFilmAnimation"
            SmFilmMoveBottom.transition = SlideTransition(direction="left")
            self.curFilmTransportBottomScreen = "screenButtonsLoadFilm"

        if self.fmc_State == 5:
            SmFilmMoveCenter.transition = NoTransition()
            self.curFilmTransportCenterScreen = "screenFilmAnimation"
            self.curFilmTransportBottomScreen = "screenInitFilm"

        if self.fmc_State == 10:
            SmFilmMoveCenter.transition = NoTransition()
            self.curFilmTransportCenterScreen = "screenFilmAnimation"
            SmFilmMoveBottom.transition = SlideTransition(direction="left")
            self.curFilmTransportBottomScreen = "screenButtonsFilmIsInsert"
            if self.curMoveCommand == 0:
                self.disable_btnFilmControl = False
                self.disable_btnFilmMoveBackward = False
                self.disable_btnFilmMoveForward = False
                self.disable_btnStop = False
                self.disable_btnFreeRun = False

            if self.curMoveCommand == 10 or self.curMoveCommand == 20:
                if self.curMoveCommand == 10:
                    self.filmAnimationDirection = 1
                if self.curMoveCommand == 20:
                    self.filmAnimationDirection = 2
                self.disable_btnFilmControl = True
                self.disable_btnFilmMoveBackward = True
                self.disable_btnFilmMoveForward = True
                self.disable_btnStop = False
                self.disable_btnFreeRun = True

            if self.curMoveCommand == 31 or self.curMoveCommand == 33 or self.curMoveCommand == 35:
                self.disable_btnFilmControl = True
                self.disable_btnFilmMoveBackward = True
                self.disable_btnFilmMoveForward = False
                self.disable_btnStop = False
                self.disable_btnFreeRun = True

            if self.curMoveCommand == 32 or self.curMoveCommand == 34 or self.curMoveCommand == 36:
                self.disable_btnFilmControl = True
                self.disable_btnFilmMoveBackward = False
                self.disable_btnFilmMoveForward = True
                self.disable_btnStop = False
                self.disable_btnFreeRun = True

    def on_curMoveCommand(self, instance, value):
        print("curMoveCommand changed to: " + str(self.curMoveCommand))

        if self.curMoveCommand == 0:
            self.filmAnimationDirection = 0
            self.disable_btnFilmControl = False
            self.disable_btnFilmMoveBackward = False
            self.disable_btnFilmMoveForward = False
            self.disable_btnStop = False
            self.disable_btnFreeRun = False

        if self.curMoveCommand == 10 or self.curMoveCommand == 20:
            if self.curMoveCommand == 10:
                self.filmAnimationDirection = 1
            if self.curMoveCommand == 20:
                self.filmAnimationDirection = 2
            self.disable_btnFilmControl = True
            self.disable_btnFilmMoveBackward = True
            self.disable_btnFilmMoveForward = True
            self.disable_btnStop = False
            self.disable_btnFreeRun = True

        if self.curMoveCommand == 31 or self.curMoveCommand == 33 or self.curMoveCommand == 35:
            self.filmAnimationDirection = 2
            self.disable_btnFilmControl = True
            self.disable_btnFilmMoveBackward = True
            self.disable_btnFilmMoveForward = False
            self.disable_btnStop = False
            self.disable_btnFreeRun = True

        if self.curMoveCommand == 32 or self.curMoveCommand == 34 or self.curMoveCommand == 36:
            self.filmAnimationDirection = 1
            self.disable_btnFilmControl = True
            self.disable_btnFilmMoveBackward = False
            self.disable_btnFilmMoveForward = True
            self.disable_btnStop = False
            self.disable_btnFreeRun = True

    def mainMenuControl(self, screenIndex):
        if screenIndex != self.lastScreenIndex:
            if screenIndex == 0:
                SmMainScreen.transition = SlideTransition(direction="down")
                self.curMainScreen = "screenFilmTransport"
                self.mainMenuRectPosition = 360
            if screenIndex == 1:
                if screenIndex > self.lastScreenIndex:
                    SmMainScreen.transition = SlideTransition(direction="up")
                else:
                    SmMainScreen.transition = SlideTransition(direction="down")
                self.curMainScreen = "screenCameraControl"
                self.mainMenuRectPosition = 240
            if screenIndex == 2:
                if screenIndex > self.lastScreenIndex:
                    SmMainScreen.transition = SlideTransition(direction="up")
                else:
                    SmMainScreen.transition = SlideTransition(direction="down")
                self.curMainScreen = "screenProjectControl"
                self.mainMenuRectPosition = 120
            if screenIndex == 3:
                if screenIndex > self.lastScreenIndex:
                    SmMainScreen.transition = SlideTransition(direction="up")
                else:
                    SmMainScreen.transition = SlideTransition(direction="down")
                self.curMainScreen = "screenSettings"
                self.mainMenuRectPosition = 0
        self.lastScreenIndex = screenIndex

    def updateSpoolArc(self, interval):
        if self.spoolDiameterFront > 50:
            self.arcSpoolFront = (self.spoolDiameterFront - 55) * 3.42
            self.arcColorSpoolFront = "#22f400"
        else:
            self.arcSpoolFront = 0
            self.arcColorSpoolFront = "ff0000"

        if self.spoolDiameterRear > 50:
            self.arcSpoolRear = (self.spoolDiameterRear - 55) * 3.42
            self.arcColorSpoolRear = "#22f400"
        else:
            self.arcSpoolRear = 0
            self.arcColorSpoolRear = "ff0000"

    def reboot_hmi(self):
        restart()

    def show_reboot_popup(self):
        show_restartPopup()

    def updateScreen(self):
        print("Update Screen !!!")
        App.get_running_app().root.ids.smBaseScreenID.current = "screenInitHmi"

    def sendMoveCommand(self, value):
        print("send moveCommand: " + str(value))
        client_mqtt.publish(sTopic_setMoveCommand, value)

    def visionSensorIsConnected(self):
        ping = IpCheckVisionSensor(visionSensorConnectionData["ip_address"])
        ping.start()

    def mainControllerIsConnected(self):
        ping = IpCheckMainController("192.168.0.6")
        ping.start()

    def filmMoveControllerIsConnected(self):
        ping = IpCheckFilmMoveController("192.168.0.10")
        ping.start()

    def switchIsConnected(self):
        ping = IpCheckSwitch("192.168.0.100")
        ping.start()

    def enable_filmLoadFastForward(self):
        client_mqtt.publish(sTopic_filmLoadFastForward, "true")

    def disable_filmLoadFastForward(self):
        client_mqtt.publish(sTopic_filmLoadFastForward, "false")

    def startFilmLoad(self):
        client_mqtt.publish(sTopic_setLedBrightnessWhite, "2000")
        client_mqtt.publish(sTopic_startLoadFilm, "")
        self.filmLoadAnimationPicPos = 100

    def stopFilmLoad(self):
        client_mqtt.publish(sTopic_stopLoadFilm, "")

    def startFilmInit(self):
        client_mqtt.publish(sTopic_startFilmInit, "")

    def enable_freerun(self):
        self.freeRunEnabled = True
        SmFilmMoveBottom.transition = SlideTransition(direction="down")
        self.curFilmTransportBottomScreen = "screenButtonsFilmIsInsert"
        client_mqtt.publish(sTopic_enableFreeRun, "")

    def disable_freerun_with_init_film(self):
        self.freeRunEnabled = False
        self.btnFreeRunText = "Unlock Motors"
        client_mqtt.publish(sTopic_startFilmInit, "")

    def show_screen_toggle_freerun(self):
        if self.fmc_State == 10 or self.fmc_State == 0:
            SmFilmMoveBottom.transition = SlideTransition(direction="up")
            self.curFilmTransportBottomScreen = "screenEnableFreeRun"

    def cancel_freerun(self):
        if self.fmc_State == 0:
            SmFilmMoveBottom.transition = SlideTransition(direction="down")
            self.curFilmTransportBottomScreen = "screenButtonsNoFilmInsert"
        if self.fmc_State == 10:
            SmFilmMoveBottom.transition = SlideTransition(direction="down")
            self.curFilmTransportBottomScreen = "screenButtonsFilmIsInsert"

    def disable_freerun(self):
        self.freeRunEnabled = False
        client_mqtt.publish(sTopic_disableFreeRun, "")
        # client_mqtt.publish(sTopic_startFilmInit, "")

    def toggleDownHolder(self):
        if self.curDhPosition:
            self.moveDhDown()
        else:
            self.moveDhUp()

    def moveDhUp(self):
        client_mqtt.publish(sTopic_setDhPosition, "Up")
        self.curDhPosition = True
        self.dhButtonText = "LOWER GLASS"

    def moveDhDown(self):
        client_mqtt.publish(sTopic_setDhPosition, "Down")
        self.curDhPosition = False
        self.dhButtonText = "RISE GLASS"

    def setLedColor(self, led_color):
        self.curLedColor = led_color
        if self.curLedColor == 0:
            client_mqtt.publish(sTopic_setLedColor, "Off")
        if self.curLedColor == 1:
            self.set_ledBrightnessSlider = (self.ledBrightnessWhite - 500) / 20
            client_mqtt.publish(sTopic_setLedColor, "White")
        if self.curLedColor == 2:
            self.set_ledBrightnessSlider = (self.ledBrightnessRed - 500) / 20
            client_mqtt.publish(sTopic_setLedColor, "Red")
        if self.curLedColor == 3:
            self.set_ledBrightnessSlider = (self.ledBrightnessGreen - 500) / 20
            client_mqtt.publish(sTopic_setLedColor, "Green")
        if self.curLedColor == 4:
            self.set_ledBrightnessSlider = (self.ledBrightnessBlue - 500) / 20
            client_mqtt.publish(sTopic_setLedColor, "Blue")

    def toggleLight(self, widget):
        if widget.state == "normal":
            print("switch Light Off")
            client_mqtt.publish(sTopic_setLedColor, "Off")
        if widget.state == "down":
            print("switch Light On")
            client_mqtt.publish(sTopic_setLedColor, "White")

    def toggleLedColor(self, widget):
        if widget.state == "normal":
            print("show screen filmTransport")
            SmFilmMoveCenter.transition = SlideTransition(direction="up")
            self.curFilmTransportCenterScreen = "screenFilmAnimation"
        if widget.state == "down":
            print("show screen led_color")
            SmFilmMoveCenter.transition = SlideTransition(direction="down")
            self.curFilmTransportCenterScreen = "screenSelectLedColor"

    def on_curFilmSpeed(self, instance, value):
        if self.curFilmSpeed > 0:
            filmAnimationDelay = 1 / (self.curFilmSpeed / 100)
            # print("filmAnimationDelay: " + str(filmAnimationDelay))
            # App.get_running_app().timerUpdateAnimation.unsubscribe()
            # App.get_running_app().timerUpdateAnimation = Clock.schedule_interval(self.updateAnimation, 1/10)

    def updateInitHmiAnimation(self, dt):
        if self.initHmiAnimationPicPos > 175:
            self.initHmiAnimationPicPos = 100
        self.initHmiAnimationBottomImgSource = self.initHmiAnimationBottomPath + str(self.initHmiAnimationPicPos) + ".png"
        self.initHmiAnimationTopImgSource = self.initHmiAnimationTopPath + str(self.initHmiAnimationPicPos) + ".png"
        self.initHmiAnimationPicPos += 1

    def updateFilmLoadAnimation(self, dt):
        if self.filmLoadAnimationPicPos > 324:
            self.filmLoadAnimationPicPos = 100
        self.filmLoadAnimationBottomImgSource = self.filmLoadAnimationBottomPath + str(self.filmLoadAnimationPicPos) + ".png"
        self.filmLoadAnimationTopImgSource = self.filmLoadAnimationTopPath + str(self.filmLoadAnimationPicPos) + ".png"
        self.filmLoadAnimationPicPos += 1

    def updateFilmMoveAnimation(self, dt):
        if self.curFilmMoveDirection == 1:
            self.filmMoveAnimationPicPos += 1
            if self.filmMoveAnimationPicPos > 174:
                self.filmMoveAnimationPicPos = 100
            self.filmMoveAnimationBottomImgSource = self.filmMoveAnimationBottomPath + str(self.filmMoveAnimationPicPos) + ".png"
            self.filmMoveAnimationTopImgSource = self.filmMoveAnimationTopPath + str(self.filmMoveAnimationPicPos) + ".png"

        if self.curFilmMoveDirection == 2:
            self.filmMoveAnimationPicPos -= 1
            if self.filmMoveAnimationPicPos < 100:
                self.filmMoveAnimationPicPos = 174
            self.filmMoveAnimationBottomImgSource = self.filmMoveAnimationBottomPath + str(self.filmMoveAnimationPicPos) + ".png"
            self.filmMoveAnimationTopImgSource = self.filmMoveAnimationTopPath + str(self.filmMoveAnimationPicPos) + ".png"

    def setLedBrightness(self, led_brightness):
        min_brightness = 500

        t_led_color = min_brightness + led_brightness * 20

        if self.curLedColor == 1:
            client_mqtt.publish(sTopic_setLedBrightnessWhite, str(t_led_color))
        if self.curLedColor == 2:
            client_mqtt.publish(sTopic_setLedBrightnessRed, str(t_led_color))
        if self.curLedColor == 3:
            client_mqtt.publish(sTopic_setLedBrightnessGreen, str(t_led_color))
        if self.curLedColor == 4:
            client_mqtt.publish(sTopic_setLedBrightnessBlue, str(t_led_color))

    def selectCameraTypeScreenToggle(self, show):
        self.updateList = True
        if show == True:
            print("show screen selectCameraType")
            SmFilmMoveCenter.transition = SlideTransition(direction="left")
            self.curFilmTransportCenterScreen = "screenSelectCameraType"
            SmFilmMoveBottom.transition = SlideTransition(direction="left")
            self.curFilmTransportBottomScreen = "screenButtonsSelectCameraType"
        else:
            print("show screen filmMove")
            SmFilmMoveCenter.transition = SlideTransition(direction="right")
            self.curFilmTransportCenterScreen = "screenFilmAnimation"
            SmFilmMoveBottom.transition = SlideTransition(direction="right")
            self.curFilmTransportBottomScreen = "screenButtonsFilmIsInsert"

    def checkInitHmiFinished(self):
        if App.get_running_app().mainControllerConnected:
            MainApp.checkMainControllerIsConnected.cancel()

        if App.get_running_app().filmMoveControllerConnected:
            MainApp.checkFilmMoveControllerIsConnected.cancel()

        if App.get_running_app().switchConnected:
            MainApp.checkSwitchIsConnected.cancel()

        if App.get_running_app().visionSensorConnected:
            MainApp.checkVisionSensorIsConnected.cancel()

        if App.get_running_app().mainControllerConnected and App.get_running_app().filmMoveControllerConnected:
            if App.get_running_app().switchConnected and App.get_running_app().visionSensorConnected:
                App.get_running_app().initHmiDisplayFinished = True
                print("switchScreen to HomeScreen")
                FullScreenManager.transition = FadeTransition()
                App.get_running_app().curFullScreen = "fullScreenHmiMenu"
                App.get_running_app().vs_load_job_list()
                vs_read_current_job_information()
                MainApp.checkInitHmiIsFinished.cancel()

    checkVisionSensorIsConnected = Clock.schedule_interval(visionSensorIsConnected, 8)
    checkMainControllerIsConnected = Clock.schedule_interval(mainControllerIsConnected, 6)
    checkFilmMoveControllerIsConnected = Clock.schedule_interval(filmMoveControllerIsConnected, 5)
    checkSwitchIsConnected = Clock.schedule_interval(switchIsConnected, 7)
    checkInitHmiIsFinished = Clock.schedule_interval(checkInitHmiFinished, 3)

    def update_preset_list(self):
        self.updateList = False
        self.vs_load_job_list()
        self.updateList = True

    def vs_load_job_list(self):
        self.vs_presets.clear()
        for i in range(0, 50):
            t_presets = read_job_information(100 + i)
            if t_presets[0] == "1":
                print("add Job to List: " + str(t_presets[1]))
                self.vs_presets.append(t_presets[1])
            else:
                break
        self.mqtt_publish_vs_job_list()

    def mqtt_publish_vs_job_list(self):
        json_vs_job_list = json.dumps(self.vs_presets)
        client_mqtt.publish(sTopic_availableJobs, json_vs_job_list)

    def vs_show_load_preset_screen(self):
        SmFilmMoveCenter.transition = NoTransition()
        self.curFilmTransportCenterScreen = "screenFilmAnimation"
        SmFilmMoveBottom.transition = SlideTransition(direction="left")
        self.curFilmTransportBottomScreen = "screenSetVisionSensorSettings"

    def on_vs_load_preset_state(self, instance, value):
        print("vsLoadPresetState: " + str(self.vs_load_preset_state))
        if self.vs_load_preset_state == 5:
            SmFilmMoveBottom.transition = SlideTransition(direction="left")
            self.curFilmTransportBottomScreen = "screenButtonsFilmIsInsert"

    def vs_set_job(self):
        # self.vs_ui_selected_film_type = self.vs_ui_selected_film_id
        if self.vs_ui_selected_film_type == 0:
            self.vs_set_job_id = self.vs_ui_selected_film_id
        else:
            self.vs_set_job_id = self.vs_ui_selected_film_id + 100
        self.vs_load_preset_state = 1

    def on_vs_set_job_id(self, instance, value):
        print("setJobId: " + str(self.vs_set_job_id))
        t = Thread(target=vs_load_program, args=(self.vs_set_job_id,))
        t.start()

    def on_vs_cur_job_id(self,instance, value):
        print("curJobId: " + str(self.vs_cur_job_id))
        client_mqtt.publish(sTopic_curVsJobId, str(self.vs_cur_job_id))

    def on_vs_cur_film_name(self,instance, value):
        client_mqtt.publish(sTopic_getCurJobName, self.vs_cur_film_name)

    def build(self):
        # Clock.schedule_interval(self.updateSpoolArc, 0.2)
        self.moveDhUp()
        timerUpdateAnimation = Clock.schedule_interval(self.updateFilmMoveAnimation, 1 / 25)
        timerUpdateFilmLoadAnimation = Clock.schedule_interval(self.updateFilmLoadAnimation, 1 / 25)
        timerUpdateInitHmiAnimation = Clock.schedule_interval(self.updateInitHmiAnimation, 1 / 20)
        return BaseScreen()


if __name__ == "__main__":
    try:
        MainApp().run()
    finally:
        program_close_handler()
