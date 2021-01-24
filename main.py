from kivy.app import App
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition, NoTransition
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty, StringProperty, ColorProperty, ListProperty
from kivy.animation import Animation
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.effectwidget import EffectWidget
from kivy.utils import get_color_from_hex
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.core.image import Image as Image
import os
from sys import platform
import paho.mqtt.client as mqtt
from configparser import ConfigParser
from enum import Enum
import sys

from telnetlib import Telnet
import getpass

from opcua import Client
from opcua import ua

import threading

from ping3 import ping
import pyads

tn_HOST = "192.168.0.30"
tn_user = "admin"
tn_password = ""

os.environ["KIVY_IMAGE"] = "pil"

enablePlcCommunication = False

cp_VisionSensor = ConfigParser()
cp_Mqtt = ConfigParser()

cp_VisionSensor.read("settings/config_visionsensor.ini")
visionSensorConnectionData = cp_VisionSensor["VisionSensor"]
client = Client("opc.tcp://" + visionSensorConnectionData["ip_address"] + ":4840")

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
sTopic_startLoadFilm =  mqtt_configData["sTopic_startLoadFilm"]
sTopic_stopLoadFilm =  mqtt_configData["sTopic_stopLoadFilm"]
sTopic_filmLoadFastForward = mqtt_configData["sTopic_filmLoadFastForward"]
sTopic_enableFreeRun = mqtt_configData["sTopic_enableFreeRun"]
sTopic_disableFreeRun = mqtt_configData["sTopic_disableFreeRun"]

currentLedColor = 0
currentDhPosition = ""


def write_opc_setting_float(node_id, value):
    var = client.get_node(node_id)
    dv = ua.DataValue(ua.Variant(float(value), ua.VariantType.Float))
    dv.ServerTimestamp = None
    dv.SourceTimestamp = None
    var.set_value(dv)
    print(node_id + ": " + str(var.get_value()))


def write_opc_setting_int32(node_id, value):
    var = client.get_node(node_id)
    dv = ua.DataValue(ua.Variant(int(value), ua.VariantType.Int32))
    dv.ServerTimestamp = None
    dv.SourceTimestamp = None
    var.set_value(dv)
    print(node_id + ": " + str(var.get_value()))


def write_opc_setting_bool(node_id, value):
    print("writeBool")
    var = client.get_node(node_id)
    # var.set_attribute(ua.AttributeIds.value, ua.DataValue(False))
    dv = ua.DataValue(ua.Variant(True))
    dv.ServerTimestamp = None
    dv.SourceTimestamp = None
    test = var.set_value(dv)
    print(test)
    print(node_id + ": " + str(var.get_value()))


def load_job(node_id, value):
    # node_id = "ns=2;s=LoadJob"
    var = client.get_node(node_id)
    dv = ua.DataValue(ua.Variant(value))
    dv.ServerTimestamp = None
    dv.SourceTimestamp = None
    output = var.call_method(node_id, dv)
    print(output)


def write_settings_vsensor_positive():
    try:
        client.connect()
        visionSensorSettings_Positive = cp_VisionSensor["VisionSensor_Positive"]
        write_opc_setting_int32("ns=2;s=Acquisition.Auto_Exposure", 0)
        write_opc_setting_float("ns=2;s=Acquisition.Exposure_Time", visionSensorSettings_Positive["exposureTime"])
        write_opc_setting_float("ns=2;s=Acquisition.Target_Image_Brightness",
                                visionSensorSettings_Positive["targetImageBrightness"])
        write_opc_setting_int32("ns=2;s=Acquisition.Autofocus", 0)
        write_opc_setting_int32("ns=2;s=Edge_1.Edge_Contrast", visionSensorSettings_Positive["edgeContrast"])
        write_opc_setting_int32("ns=2;s=Edge_2.Edge_Contrast", visionSensorSettings_Positive["edgeContrast"])
        write_opc_setting_int32("ns=2;s=Edge_1.Edge_Transition", visionSensorSettings_Positive["edgeTransition"])
        write_opc_setting_int32("ns=2;s=Edge_2.Edge_Transition", visionSensorSettings_Positive["edgeTransition"])
        write_opc_setting_float("ns=2;s=Brightness_Gap.Minimum", 0)
        write_opc_setting_float("ns=2;s=Brightness_Gap.Maximum",
                                visionSensorSettings_Positive["brightnessCheck_SwitchValue"])
        write_opc_setting_float("ns=2;s=Brightness_Image.Minimum",
                                visionSensorSettings_Positive["brightnessCheck_SwitchValue"])
        write_opc_setting_float("ns=2;s=Brightness_Image.Maximum", 255)
    except:
        print("Cannot write Data to Visionsensor")
    finally:
        client.disconnect()


def load_job_from_id(job_id):
    t_job_id = str(job_id)
    tn = Telnet(tn_HOST, 23)
    # Login to Sensor
    print("Telnet connected")
    tn.read_until(b"User: ")
    tn.write(tn_user.encode('ascii') + b"\r\n")
    tn.read_until((b"Password: "))
    tn.write(b"\r\n")
    tn.read_until(b"User Logged In\r\n")
    # Login Finished
    tn.write(b"SJ" + t_job_id.encode('ascii') + b"\r\n")
    print("set Job: " + t_job_id)
    call_ok = str(tn.read_until(b"\r\n"), 'utf-8')
    call_ok = call_ok.replace("\r\n", "")
    print("callOK: " + call_ok)
    return call_ok
    tn.close()


def get_loaded_job_id():
    cur_jobId = 0
    tn = Telnet(tn_HOST, 23)
    # Login to Sensor
    print("Telnet connected")
    tn.read_until(b"User: ")
    tn.write(tn_user.encode('ascii') + b"\r\n")
    tn.read_until((b"Password: "))
    tn.write(b"\r\n")
    tn.read_until(b"User Logged In\r\n")
    # Login Finished
    tn.write(b"GJ" + b"\r\n")
    call_ok = str(tn.read_until(b"\r\n"), 'utf-8')
    call_ok = call_ok.replace("\r\n", "")
    print("callOK: " + call_ok)
    if call_ok == "1":
        cur_jobId = str(tn.read_until(b"\r\n"), 'utf-8')
        cur_jobId = cur_jobId.replace("\r\n", "")
        print("current loaded jobId: " + cur_jobId)
    else:
        cur_jobId = 0
    return call_ok, cur_jobId
    tn.close()


def read_job_information(job_id):
    t_job_id = str(job_id)
    tn = Telnet(tn_HOST, 23)
    # Login to Sensor
    print("Telnet connected")
    tn.read_until(b"User: ")
    tn.write(tn_user.encode('ascii') + b"\r\n")
    tn.read_until((b"Password: "))
    tn.write(b"\r\n")
    tn.read_until(b"User Logged In\r\n")
    #Login Finished
    tn.write(b"RJ" + t_job_id.encode('ascii') + b"\r\n")
    print("get infos from Job" + t_job_id)
    call_ok = str(tn.read_until(b"\r\n"), 'utf-8')
    call_ok = call_ok.replace("\r\n", "")
    print("callOK: " + call_ok)
    if call_ok == "1":
        filename = str(tn.read_until(b"\r\n"), 'utf-8')
        filename = filename.replace("\r\n", "")
        filename = filename.replace(".job", "")
        filename = filename.replace("_", " ")
        file_data = filename.split("-")
        print("filename: " + filename)
        job_size = str(tn.read_until(b"\r\n"), 'utf-8')
        job_size = job_size.replace("\r\n", "")
        print("jobSize: " + job_size)
    else:
        file_data = ""
    return call_ok, file_data
    tn.close()


def set_visionsensor_online_state(value):
    tValue = str(value)
    tn = Telnet(tn_HOST, 23)
    # Login to Sensor
    print("Telnet connected")
    tn.read_until(b"User: ")
    tn.write(tn_user.encode('ascii') + b"\r\n")
    tn.read_until((b"Password: "))
    tn.write(b"\r\n")
    tn.read_until(b"User Logged In\r\n")
    # Login Finished
    tn.write(b"SO" + tValue.encode('ascii') + b"\r\n")
    print("set sensor_state to: " + tValue)
    call_ok = str(tn.read_until(b"\r\n"), 'utf-8')
    call_ok = call_ok.replace("\r\n", "")
    print("callOK: " + call_ok)
    return call_ok
    tn.close()


def write_settings_vsensor_negative():
    try:
        client.connect()
        visionSensorSettings_Negative = cp_VisionSensor["VisionSensor_Negative"]
        write_opc_setting_int32("ns=2;s=Acquisition.Auto_Exposure", 0)
        write_opc_setting_float("ns=2;s=Acquisition.Exposure_Time", visionSensorSettings_Negative["exposureTime"])
        write_opc_setting_float("ns=2;s=Acquisition.Target_Image_Brightness",
                                visionSensorSettings_Negative["targetImageBrightness"])
        write_opc_setting_int32("ns=2;s=Acquisition.Autofocus", 0)
        write_opc_setting_int32("ns=2;s=Edge_1.Edge_Contrast", visionSensorSettings_Negative["edgeContrast"])
        write_opc_setting_int32("ns=2;s=Edge_2.Edge_Contrast", visionSensorSettings_Negative["edgeContrast"])
        write_opc_setting_int32("ns=2;s=Edge_1.Edge_Transition", visionSensorSettings_Negative["edgeTransition"])
        write_opc_setting_int32("ns=2;s=Edge_2.Edge_Transition", visionSensorSettings_Negative["edgeTransition"])
        write_opc_setting_float("ns=2;s=Brightness_Gap.Minimum",
                                visionSensorSettings_Negative["brightnessCheck_SwitchValue"])
        write_opc_setting_float("ns=2;s=Brightness_Gap.Maximum", 255)
        write_opc_setting_float("ns=2;s=Brightness_Image.Minimum", 0)
        write_opc_setting_float("ns=2;s=Brightness_Image.Maximum",
                                visionSensorSettings_Negative["brightnessCheck_SwitchValue"])
    except:
        print("Cannot write Data to Visionsensor")
    finally:
        client.disconnect()


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
            #App.get_running_app().btnDhState = "normal"
            # print("/////incomingMessage // dhpos: UP")
        else:
            App.get_running_app().curDhPosition = False
            #App.get_running_app().btnDhState = "down"
            # print("/////incomingMessage // dhpos: DOWN")

    if msg.topic == sTopic_getMoveCommand:
        t_cur_message = int(cur_message)
        if t_cur_message == 0:
            print("set_btnFilmControl to False")
            App.get_running_app().disable_btnFilmControl = False
            App.get_running_app().disable_btnFilmMoveForward = False
            App.get_running_app().disable_btnFilmMoveBackward = False
            BaseApp.filmInitIsFinished = False
            # ScreenInitFilm.stop_init_film()

        if t_cur_message == 60:
            BaseApp.filmInitIsFinished = False
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


if enablePlcCommunication == True:
    if platform == "linux" or platform == "linux2":
        pyads.add_route("5.71.85.220.1.1", "192.168.0.10")

    plc = pyads.Connection('5.71.85.220.1.1', 851, "192.168.0.10")
    plc.open()

    print(plc.read_by_name("MAIN.curFilmPosition", pyads.PLCTYPE_INT))
    print(plc.read_state())
    # plc.write_control(pyads.ADSSTATE_RUN, plc.read_state()[0], 0, pyads.PLCTYPE_INT)


class restartPopup(FloatLayout):
    pass


def show_restartPopup():
    show = restartPopup()
    popupWindow = Popup(title="Warning - Please Confirm", content=show, size_hint=(None, None), size=(400, 200))
    popupWindow.open()


class enableFreeRunPopup(FloatLayout):
        pass

class disableFreeRunPopup(FloatLayout):
    pass


def show_enable_freerun_popup():
    show = enableFreeRunPopup()
    global efr_popupWindow
    efr_popupWindow = Popup(title="Warning - Please Confirm", content=show, size_hint=(None, None), size=(400, 200))
    efr_popupWindow.open()


def show_disable_freerun_popup():
    show = disableFreeRunPopup()
    global efr_popupWindow
    efr_popupWindow = Popup(title="Leave FreeRun-Mode", content=show, size_hint=(None, None), size=(400, 200))
    efr_popupWindow.open()


def restart():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    import subprocess
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print(output)


class BaseScreenManager(ScreenManager):
    def __init__(self, **kwargs):
        super(BaseScreenManager, self).__init__(**kwargs)
        self.add_widget(ScreenInitHmi(name='screenInitHmi'))
        #self.add_widget(BaseScreen(name="screenBase"))


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




class BaseScreen(Screen):
    pass


class HomeScreen(Screen):
    pass


class ScreenInitHmi(Screen):
    pass


class FilmTransportControl(Screen):
    pass


class CameraControl(Screen):
    pass


class ProjectControl(Screen):
    pass


class ScreenSettings(Screen):
    pass


class VisButton(ToggleButton):
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


class ScreenSelectCameraType(Screen):
    def __init__(self, **kwargs):
        super(ScreenSelectCameraType, self).__init__(**kwargs)
        fillUpItems = 12 - len(BaseApp.vs_presets)
        for i in BaseApp.vs_presets:
            self.ids.rvSelectCameraType.data.append({"text": i[1] + "\n" + i[2], "presetId": i[0]})
        for i in range(fillUpItems):
            self.ids.rvSelectCameraType.data.append({"text": "", "presetId": 0})


class SelectCameraButton(ToggleButton):
    def on_press(self):
        print(self.presetId)
        BaseApp.vs_selected_preset_temp = self.presetId


class DhButton(Button):
    curDhPosition = BooleanProperty()

    def on_curDhPosition(self, *kwargs):
        if not self.curDhPosition:
            dhBtnAni = Animation(arrowAngle=180, duration=0.2)
            dhBtnAni.start(self)
        if self.curDhPosition:
            dhBtnAni = Animation(arrowAngle=0, duration=0.2)
            dhBtnAni.start(self)


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


class ScreenInitFilm(Screen):
    # timer_check_init_finished = ""
    # timer_timeout = ""

    def start_init_film(self):
        self.timer_check_init_finished = Clock.schedule_interval(self.check_init_film_finished, 0.5)
        self.timer_timeout = Clock.schedule_once(self.init_film_timeout, 20)

    def check_init_film_finished(self, dt):
        if App.get_running_app().fmc_State == 10:
            print("Init finished")
            App.get_running_app().root.ids.smBaseScreen.transition.direction = "left"
            App.get_running_app().root.ids.smBaseScreen.current = "screenManualControl"
            self.timer_check_init_finished.cancel()
            self.timer_timeout.cancel()
        if App.get_running_app().fmc_State == 3:
            print("Init-Film fail - film is not correct on front-spool")
            App.get_running_app().root.ids.smBaseScreen.transition.direction = "left"
            App.get_running_app().root.ids.smBaseScreen.current = "screenHome"
            self.timer_check_init_finished.cancel()
            self.timer_timeout.cancel()

    def init_film_timeout(self, interval):
        self.timer_check_init_finished.cancel()
        self.timer_timeout.cancel()
        App.get_running_app().root.ids.smBaseScreen.transition.direction = "right"
        App.get_running_app().root.ids.smBaseScreen.current = "screenHome"
        print("Init-Film-TimeOut....")


    def stop_init_film(self):
        self.timer_check_init_finished.cancel()
        self.timer_timeout.cancel()
        print("Stop Init Film....")

class MainScreen(Screen):
    w_dhStatus = ObjectProperty(0)
    w_dhButton = ObjectProperty(0)
    w_LightToggle = ObjectProperty(None)
    w_MenuSelectLedColor = ObjectProperty(None)

    def enableSettings_Positive(self, widget):
        print("enableSettings_Positive")
        write_settings_vsensor_positive()

    def enableSettings_Negative(self, widget):
        print("enableSettings_Negative")
        write_settings_vsensor_negative()

    def dhAnimationToggle(self, widget):
        # print("start Animation")
        if widget.state == "normal":
            dh_ani = Animation(setDhPosition=18, duration=0.2)
            dh_ani.start(self.w_dhStatus)
            dhBtnAni = Animation(arrowAngle=180, duration=0.2)
            dhBtnAni.start(self.w_dhButton)
        if widget.state == "down":
            dh_ani = Animation(setDhPosition=0, duration=0.2)
            dh_ani.start(self.w_dhStatus)
            dhBtnAni = Animation(arrowAngle=0, duration=0.2)
            dhBtnAni.start(self.w_dhButton)

    def setDhPositionToggle(self, widget):
        print("###################################################")
        if widget.state == "normal":
            print("set DH-Position to Up / curDhPos: " + currentDhPosition)
            App.get_running_app().root.ids.btnDhState = "normal"
            client_mqtt.publish(sTopic_setDhPosition, "Up")
        if widget.state == "down":
            print("set DH-Position to Down / curDhPos: " + currentDhPosition)
            App.get_running_app().root.ids.btnDhState = "down"
            client_mqtt.publish(sTopic_setDhPosition, "Down")

    def switchLightToggle(self, widget):
        # print("curLightColor: " + str(BaseApp.curLedColor))
        if widget.state == "down":
            print("switch Light On")
            client_mqtt.publish(sTopic_setLedColor, "White")
        else:
            print("switch Light Off")
            client_mqtt.publish(sTopic_setLedColor, "Off")

    def showSelectColorMenu(self):
        print("show SelectLedMenu")
        ani_fade_in = Animation(opacity=1.0, y=170, t='out_circ', duration=0.2)
        ani_fade_in.start(self.w_MenuSelectLedColor)
        self.w_MenuSelectLedColor.isVisible = True

    def hideSelectColorMenu(self):
        print("Hide SelectLedMenu")
        ani_fade_in = Animation(opacity=0.0, y=237, t='out_quad', duration=0.2)
        ani_fade_in.start(self.w_MenuSelectLedColor)
        self.w_MenuSelectLedColor.isVisible = False

    def switchShowMenuSelectLedColor(self, widget):
        if not self.w_MenuSelectLedColor.isVisible:
            self.showSelectColorMenu()
        else:
            self.hideSelectColorMenu()

    def sendMoveCommand(self, value):
        client_mqtt.publish(sTopic_setMoveCommand, value)

    def pressLedButtonWhite(self, widget):
        print("LedWhite pressed")
        self.w_MenuSelectLedColor.selectedColor = 1
        client_mqtt.publish(sTopic_setLedColor, "White")
        self.hideSelectColorMenu()

    def pressLedButtonRed(self, widget):
        print("LedRed pressed")
        self.w_MenuSelectLedColor.selectedColor = 2
        client_mqtt.publish(sTopic_setLedColor, "Red")
        self.hideSelectColorMenu()

    def pressLedButtonGreen(self, widget):
        print("LedGreen pressed")
        self.w_MenuSelectLedColor.selectedColor = 3
        client_mqtt.publish(sTopic_setLedColor, "Green")
        self.hideSelectColorMenu()

    def pressLedButtonBlue(self, widget):
        print("LedBlue pressed")
        self.w_MenuSelectLedColor.selectedColor = 4
        client_mqtt.publish(sTopic_setLedColor, "Blue")
        self.hideSelectColorMenu()


class SelectFilmInitMethod(Screen):
    pass

class ScreenLoadFilm(Screen):
    pass

class BaseScreen(FloatLayout):
    pass


def program_close_handler():
    if client_mqtt.is_connected():
        client_mqtt.disconnect()


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


class BaseApp(App):
    curDhPosition = BooleanProperty()
    btnDhArrowAngle = NumericProperty()
    dhButtonText = StringProperty()

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
    arcColorSpoolFront = StringProperty("#ff0000")
    arcColorSpoolRear = StringProperty("#ff0000")
    baseColor = ColorProperty("#2699fb")
    baseGrey = ColorProperty("#464646")
    baseWhite = ColorProperty("#FFFFFF")
    baseBlack = ColorProperty("#000000")
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

    mainMenuRectPosition = NumericProperty(360)
    filmAnimationCurPicPos = 0
    filmAnimationCurImgSource = StringProperty("pictures/filmAnimation/Film Transport0.png")
    filmAnimationDelay = 1/25

    lastScreenIndex = 0
    curFilmTransportCenterScreen = StringProperty("screenFilmAnimation")
    curFilmTransportBottomScreen = StringProperty("screenButtonsNoFilmInsert")

    vs_presets = []
    vs_selected_preset_temp = 0
    vs_selected_preset = 0
    vs_selected_film_type_temp = NumericProperty(0)
    vs_selected_film_type = 0
    vs_loaded_film_name = StringProperty("")

    def on_selectedCameraType(self, instance, value):
        print("cameraType changed to: " + str(self.selectedCameraType))

    def on_curLedColor(self, instance, value):
        print("ledColor changed to: " + str(self.curLedColor))

    def on_fmc_State(self, instance, value):
        print ("fmc-State changed to: " + str(self.fmc_State))

        if self.fmc_State == 0:
            self.filmAnimationDirection = 0
            self.disable_btnFilmControl = True
            self.disable_btnFilmMoveBackward = True
            self.disable_btnFilmMoveForward = True
            self.disable_btnFreeRun = False
            self.disable_btnStop = True

        if self.fmc_State == 1:
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

        if self.fmc_State < 4:
            self.curFilmTransportBottomScreen = "screenButtonsNoFilmInsert"

        if self.fmc_State == 4:
            SmFilmMoveCenter.transition = NoTransition()
            self.curFilmTransportCenterScreen = "screenLoadFilmAnimation"
            self.curFilmTransportBottomScreen = "screenButtonsLoadFilm"

        if self.fmc_State == 5:
            SmFilmMoveCenter.transition = NoTransition()
            self.curFilmTransportCenterScreen = "screenFilmAnimation"
            self.curFilmTransportBottomScreen = "screenInitFilm"

        if self.fmc_State == 10:
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
        print ("curMoveCommand changed to: " + str(self.curMoveCommand))

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
                App.get_running_app().root.ids.smMainMenu.transition.direction = "down"
                App.get_running_app().root.ids.smMainMenu.current = "screenFilmTransport"
                self.mainMenuRectPosition = 360
            if screenIndex == 1:
                if screenIndex > self.lastScreenIndex:
                    App.get_running_app().root.ids.smMainMenu.transition.direction = "up"
                else:
                    App.get_running_app().root.ids.smMainMenu.transition.direction = "down"
                App.get_running_app().root.ids.smMainMenu.current = "screenCameraControl"
                self.mainMenuRectPosition = 240
            if screenIndex == 2:
                if screenIndex > self.lastScreenIndex:
                    App.get_running_app().root.ids.smMainMenu.transition.direction = "up"
                else:
                    App.get_running_app().root.ids.smMainMenu.transition.direction = "down"
                App.get_running_app().root.ids.smMainMenu.current = "screenProjectControl"
                self.mainMenuRectPosition = 120
            if screenIndex == 3:
                if screenIndex > self.lastScreenIndex:
                    App.get_running_app().root.ids.smMainMenu.transition.direction = "up"
                else:
                    App.get_running_app().root.ids.smMainMenu.transition.direction = "down"
                App.get_running_app().root.ids.smMainMenu.current = "screenSettings"
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
        App.get_running_app().root.ids.smBaseScreen.current = "screenInitHmi"

    def showFilmControlScreen(self):
        if self.fmc_State == 0:
            App.get_running_app().root.ids.smBaseScreen.transition.direction = "left"
            App.get_running_app().root.ids.smBaseScreen.current = "screenInitFilmSelector"
        if self.fmc_State > 0:
            App.get_running_app().root.ids.smBaseScreen.transition.direction = "left"
            App.get_running_app().root.ids.smBaseScreen.current = "screenManualControl"

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
        client_mqtt.publish(sTopic_startLoadFilm, "")

    def stopFilmLoad(self):
        client_mqtt.publish(sTopic_stopLoadFilm, "")

    def startFilmInit(self):
        client_mqtt.publish(sTopic_startFilmInit, "")

    def show_unlock_motors_popup(self):
        print ("fmcState: " + str(self.fmc_State))
        if self.fmc_State > 1:
            show_enable_freerun_popup()
        if self.fmc_State == 1:
            show_disable_freerun_popup()

    def enable_freerun(self):
        self.freeRunEnabled = True
        self.btnFreeRunText = "Lock Motors"
        client_mqtt.publish(sTopic_enableFreeRun, "")
        efr_popupWindow.dismiss()

    def disable_freerun_with_init_film(self):
        self.freeRunEnabled = False
        self.btnFreeRunText = "Unlock Motors"
        client_mqtt.publish(sTopic_startFilmInit, "")
        efr_popupWindow.dismiss()

    def disable_freerun(self):
        self.freeRunEnabled = False
        self.btnFreeRunText = "Unlock Motors"
        client_mqtt.publish(sTopic_disableFreeRun, "")

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

    def setLedColor(self, ledColor):
        self.curLedColor = ledColor
        if self.curLedColor == 0:
            client_mqtt.publish(sTopic_setLedColor, "Off")
        if self.curLedColor == 1:
            client_mqtt.publish(sTopic_setLedColor, "White")
        if self.curLedColor == 2:
            client_mqtt.publish(sTopic_setLedColor, "Red")
        if self.curLedColor == 3:
            client_mqtt.publish(sTopic_setLedColor, "Green")
        if self.curLedColor == 4:
            client_mqtt.publish(sTopic_setLedColor, "Blue")

    def on_curFilmSpeed(self, instance, value):
        if self.curFilmSpeed > 0:
            filmAnimationDelay = 1/(self.curFilmSpeed / 100)
            # print("filmAnimationDelay: " + str(filmAnimationDelay))
            # App.get_running_app().timerUpdateAnimation.unsubscribe()
            # App.get_running_app().timerUpdateAnimation = Clock.schedule_interval(self.updateAnimation, 1/10)

    def updateAnimation(self, dt):
        if self.curFilmMoveDirection == 1:
            self.filmAnimationCurPicPos += 1
            if self.filmAnimationCurPicPos > 74:
                self.filmAnimationCurPicPos = 0
            self.filmAnimationCurImgSource = "pictures/filmAnimation/Film Transport" + str(self.filmAnimationCurPicPos) + ".png"

        if self.curFilmMoveDirection == 2:
            self.filmAnimationCurPicPos -= 1
            if self.filmAnimationCurPicPos < 0:
                self.filmAnimationCurPicPos = 74
            self.filmAnimationCurImgSource = "pictures/filmAnimation/Film Transport" + str(self.filmAnimationCurPicPos) + ".png"

    def setLedBrightness(self, ledBrightness):
        minBrightness = 500

        if self.curLedColor == 1:
            client_mqtt.publish(sTopic_setLedBrightnessWhite, str(minBrightness + ledBrightness * 20))
        if self.curLedColor == 2:
            client_mqtt.publish(sTopic_setLedBrightnessRed, str(minBrightness + ledBrightness * 20))
        if self.curLedColor == 3:
            client_mqtt.publish(sTopic_setLedBrightnessGreen, str(minBrightness + ledBrightness * 20))
        if self.curLedColor == 4:
            client_mqtt.publish(sTopic_setLedBrightnessBlue, str(minBrightness + ledBrightness * 20))

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
            print("show screen ledColor")
            SmFilmMoveCenter.transition = SlideTransition(direction="down")
            self.curFilmTransportCenterScreen = "screenSelectLedColor"

    def selectCameraTypeScreenToggle(self, show):
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
            BaseApp.checkMainControllerIsConnected.cancel()

        if App.get_running_app().filmMoveControllerConnected:
            BaseApp.checkFilmMoveControllerIsConnected.cancel()

        if App.get_running_app().switchConnected:
            BaseApp.checkSwitchIsConnected.cancel()

        if App.get_running_app().visionSensorConnected:
            BaseApp.checkVisionSensorIsConnected.cancel()

        if App.get_running_app().mainControllerConnected and App.get_running_app().filmMoveControllerConnected:
            if App.get_running_app().switchConnected and App.get_running_app().visionSensorConnected:
                App.get_running_app().initHmiDisplayFinished = True
                print("switchScreen to HomeScreen")
                BaseApp.checkInitHmiIsFinished.cancel()

    checkVisionSensorIsConnected = Clock.schedule_interval(visionSensorIsConnected, 8)
    checkMainControllerIsConnected = Clock.schedule_interval(mainControllerIsConnected, 6)
    checkFilmMoveControllerIsConnected = Clock.schedule_interval(filmMoveControllerIsConnected, 5)
    checkSwitchIsConnected = Clock.schedule_interval(switchIsConnected, 7)
    checkInitHmiIsFinished = Clock.schedule_interval(checkInitHmiFinished, 3)
    #timerUpdateAnimation = Clock.schedule_interval(updateAnimation, 1 / 25)

    def vs_get_current_job(self):
        cur_job_id = get_loaded_job_id()
        if cur_job_id[0] == "1":
            self.vs_selected_preset = cur_job_id[1]
            print("vs current jobId: " + cur_job_id[0])
            cur_job_data = read_job_information(self.vs_selected_preset)
            if int(cur_job_id[1]) < 200:
                self.vs_loaded_film_name = cur_job_data[1][1] + " - " + cur_job_data[1][2] + " / NEG"
            else:
                self.vs_loaded_film_name = cur_job_data[1][1] + " - " + cur_job_data[1][2] + " / POS"

    def vs_load_job_list(self):
        for i in range(0, 50):
            t_presets = read_job_information(100 + i)
            if t_presets[0] == "1":
                print("add Button: " + str(t_presets[1]))
                self.vs_presets.append(t_presets[1])
            else:
                break

    def vs_set_job(self):
        self.vs_selected_film_type = self.vs_selected_film_type_temp
        if self.vs_selected_film_type == 0:
            self.vs_selected_preset = self.vs_selected_preset_temp
        else:
            self.vs_selected_preset = self.vs_selected_preset_temp + 100
        set_visionsensor_online_state(0)
        load_job_from_id(self.vs_selected_preset)
        self.vs_get_current_job()
        set_visionsensor_online_state(1)

    def build(self):
        #Clock.schedule_interval(self.updateSpoolArc, 0.2)
        self.vs_load_job_list()
        self.vs_get_current_job()
        self.moveDhUp()
        timerUpdateAnimation = Clock.schedule_interval(self.updateAnimation, 1/25)
        return BaseScreen()


if __name__ == "__main__":
    try:
        BaseApp().run()
    finally:
        program_close_handler()
