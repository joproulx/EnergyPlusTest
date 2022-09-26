
from ssl import HAS_TLSv1_1
import matplotlib.pyplot as plt
import os
import requests
import sys
import PySimpleGUI as sg
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from threading import Thread
from threading import Lock
import time
from datetime import datetime
import matplotlib.dates as mdates
# VARS CONSTS:

# New figure and plot variables so we can manipulate them


# \\  -------- PYPLOT -------- //


lock =Lock()

# h1, = plt.plot([], [], label="Outdoor Air Temp")
# h2, = plt.plot([], [], label="Zone Temperature")
# ax = plt.gca()
# plt.title('Outdoor Temperature')
# plt.xlabel('Zone time step index')
# plt.ylabel('Temperature [C]')
# plt.legend(loc='lower right')
x = []
y_meter = []
y_outdoor = []
y_zone = []

enableOverrideOutdoorTemp = False
overrideOutdoorTemp = 0

enableOverrideIndoorTemp = False
overrideIndoorTemp = 0

meter_value = 0
current_time_str=""
got_handles = False
oa_temp_actuator = -1
oa_temp_handle = -1
zone_temp_handle = -1
count = 0
plot_update_interval = 250  # time steps
case_index_to_run = 1
if len(sys.argv) > 1:
    case_index_to_run = int(sys.argv[1])
filename_to_run = ''
zone_name = ''
if case_index_to_run == 1:
    filename_to_run = '1ZoneEvapCooler.idf'
    zone_name = 'Main Zone'
elif case_index_to_run == 2:
    filename_to_run = '1ZoneUncontrolled.idf'
    zone_name = 'Zone One'



# def update_line():
#     h1.set_xdata(x)
#     h1.set_ydata(y_outdoor)
#     h2.set_xdata(x)
#     h2.set_ydata(y_zone)
#     ax.relim()
#     ax.autoscale_view()
#     plt.draw()
#     plt.pause(0.00001)


get_by_api = False


#def get_new_outdoor_air_temp() -> float:
#    //response = requests.get('http://127.0.0.1:8000/api/outdoor_temp/')
#    //data = response.json()
#    return data['outdoor_temp']


def callback_function(s):
    global count, got_handles, oa_temp_actuator, oa_temp_handle, zone_temp_handle, oa_schedule_temp, current_time_str, meter_handle, meter_value
    if not got_handles:
        if not a.exchange.api_data_fully_ready(s):
            return

        oa_schedule_temp = a.exchange.get_actuator_handle(state, "Schedule:Constant", "Schedule Value", "HTGSETP_SCH")
        oa_temp_actuator = a.exchange.get_actuator_handle(s, "Weather Data", "Outdoor Dry Bulb", "Environment")
        oa_temp_handle = a.exchange.get_variable_handle(s, u"SITE OUTDOOR AIR DRYBULB TEMPERATURE", u"ENVIRONMENT")
        zone_temp_handle = a.exchange.get_variable_handle(s, "Zone Mean Air Temperature", zone_name)
        meter_handle = a.exchange.get_meter_handle(state, "Electricity:Facility")
        if -1 in [oa_temp_actuator, oa_temp_handle, zone_temp_handle, oa_schedule_temp]:
            print("***Invalid handles, check spelling and sensor/actuator availability")
            sys.exit(1)
        got_handles = True
    if a.exchange.warmup_flag(s):
        return
    
    #if get_by_api:
    #    a.exchange.set_actuator_value(s, oa_temp_actuator, get_new_outdoor_air_temp())
    if enableOverrideOutdoorTemp:
        a.exchange.set_actuator_value(s, oa_temp_actuator, overrideOutdoorTemp)

    if enableOverrideIndoorTemp:
        a.exchange.set_actuator_value(s, oa_schedule_temp, overrideIndoorTemp)

    
    lock.acquire()
    count += 1
    current_time_str = f'{a.exchange.year(s)}/{a.exchange.month(s)}/{a.exchange.day_of_month(s)} {a.exchange.hour(s)}:{a.exchange.minutes(s)-1}:00'

    current_time = datetime.strptime(current_time_str, '%Y/%m/%d %H:%M:%S')


    x.append(current_time)
    oa_temp = a.exchange.get_variable_value(s, oa_temp_handle)
    y_outdoor.append(oa_temp)
    zone_temp = a.exchange.get_variable_value(s, zone_temp_handle)
    meter_value = a.exchange.get_meter_value(s, meter_handle)
    meter_value = meter_value / 1000000
    #if len(y_meter) >0:
    #    y_meter.append(y_meter[len(y_meter)-1] + meter_value)
    #else:
    #    y_meter.append(meter_value)
    y_meter.append(meter_value)

    y_zone.append(zone_temp)
    lock.release()
    time.sleep(0.1)
   


# insert the repo build tree or install path into the search Path, then import the EnergyPlus API
RepoDir = ""
#RepoDir = 'C:\trusted\Programs\EnergyPlusV22-10'
sys.path.insert(0, RepoDir)
from pyenergyplus.api import EnergyPlusAPI

a = EnergyPlusAPI()
state = a.state_manager.new_state()
a.runtime.callback_begin_zone_timestep_after_init_heat_balance(state, callback_function)


def thread_function():
    result = a.runtime.run_energyplus(
        state,
        [
        '-a',
        '-w', '/trusted/Programs/EnergyPlusV22-10/WeatherData/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw',
        '-d', 'output',
        os.path.join("../../poc/EnergyPlusTest", filename_to_run)
        ]
    )
    if result != 0:
        print("Error simulating")

thread = Thread(target=thread_function, args=())
thread.start()


#plt.show()
_VARS = {'window': False,
         'fig_agg': False,
         'pltFig': False}

dataSize = 1000  # For synthetic data

# Helper Functions


def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


# \\  -------- PYSIMPLEGUI -------- //

AppFont = 'Any 16'
sg.theme('DarkTeal12')

layout = [[sg.Canvas(key='figCanvas')],
          [sg.Text(text='Current time:'), sg.Text(key='stCurrentTime', text='')],
          [sg.Text(text='Outdoor temperature:'),  sg.Checkbox(text='Override', key='stOverrideOutdoorTemp'), sg.Slider(orientation ='horizontal', key='stOutdoorTemp', range=(-50, 50)), sg.Input(key='stOutdoorTempText',size=(3, 1))],
          [sg.Text(text='Indoor set point:'),  sg.Checkbox(text='Override', key='stOverrideIndoorTemp'), sg.Slider(orientation ='horizontal', key='stIndoorTemp', range=(-50, 50)), sg.Input(key='stIndoorTempText',size=(3, 1))],
          [sg.Button('Update', font=AppFont), sg.Button('Exit', font=AppFont)]]

_VARS['window'] = sg.Window('Such Window',
                            layout,
                            finalize=True,
                            resizable=True,
                            location=(100, 100), size=(1600, 600),
                            element_justification="right")

_VARS['pltFig'], (temp_plot, meter_plot) = plt.subplots(1, 2)
_VARS['pltFig'].set_figwidth(16)
plt.gcf().autofmt_xdate()
temp_plot.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d %H:%M:%S'))
temp_plot.xaxis.set_major_locator(mdates.AutoDateLocator())
h1, = temp_plot.plot([], [], label="Outdoor Air Temp")
h2, = temp_plot.plot([], [], label="Zone Temperature")
temp_plot.set_title('Outdoor Temperature')
temp_plot.set_xlabel('Zone time step index')
temp_plot.set_ylabel('Temperature [C]')
temp_plot.legend(loc='lower right')

meter_subplot, = meter_plot.plot([], [], label="Meter")
meter_plot.xaxis.set_major_formatter(mdates.DateFormatter('%Y/%m/%d %H:%M:%S'))
meter_plot.xaxis.set_major_locator(mdates.AutoDateLocator())
meter_plot.set_title('Meter')
meter_plot.set_xlabel('Zone time step index')
meter_plot.set_ylabel('Energy KWh')
meter_plot.legend(loc='lower right')


_VARS['fig_agg'] = draw_figure(_VARS['window']['figCanvas'].TKCanvas, _VARS['pltFig'])


def updateChart():
    _VARS['fig_agg'].get_tk_widget().forget()
    h1.set_xdata(x)
    h1.set_ydata(y_outdoor)
    h2.set_xdata(x)
    h2.set_ydata(y_zone)
    meter_subplot.set_xdata(x)
    meter_subplot.set_ydata(y_meter)

    temp_plot.relim()
    temp_plot.autoscale_view()
    meter_plot.relim()
    meter_plot.autoscale_view()

    #plt.clf()
    #plt.plot(x, y_outdoor, '.k')
    plt.draw()
    #plt.pause(0.00001)
    _VARS['fig_agg'] = draw_figure(_VARS['window']['figCanvas'].TKCanvas, _VARS['pltFig'])
    
count1 = 0
    
# MAIN LOOP
while True:
    event, values = _VARS['window'].read(timeout=200)
    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    # New Button (check the layout) and event catcher for the plot update
    #if event == 'Update':
   
    enableOverrideOutdoorTemp = bool(values['stOverrideOutdoorTemp'])
    if enableOverrideOutdoorTemp == True:
        overrideOutdoorTemp = int(values['stOutdoorTemp'])
        _VARS['window']['stOutdoorTempText'].update(int(values['stOutdoorTemp']))
    
    enableOverrideIndoorTemp = bool(values['stOverrideIndoorTemp'])
    if enableOverrideIndoorTemp == True:
        overrideIndoorTemp = int(values['stIndoorTemp'])
        _VARS['window']['stIndoorTempText'].update(int(values['stIndoorTemp']))
    
    lock.acquire()
    _VARS['window']['stCurrentTime'].update(current_time_str)

    count1 = count1 + 1
    if count1 % 5 == 0:
        updateChart()
    lock.release()

_VARS['window'].close()