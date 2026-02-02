#!/usr/bin/env/python3
# File name   : WebServer.py
# Website     : www.Adeept.com
# Author      : Adeept
# Date        : 2025/04/16

import time
import threading
import os
import Info as info
from Move import RaspClaws
from Functions import Functions
import RobotLight as robotLight
import Switch as switch
import socket
import Voltage
import asyncio
import websockets
import subprocess
import json
import app
import Buzzer

steady = 0

OLED_connection = 1
try:
    import OLED
    screen = OLED.OLED_ctrl()
    screen.start()
    screen.screen_show(1, 'ADEEPT.COM')
except:
    OLED_connection = 0
    print('OLED disconnected\n')
    pass

player = Buzzer.Player()
player.start()

batteryMonitor = Voltage.BatteryLevelMonitor()
batteryMonitor.start()

robot = RaspClaws()
robot.start()

fuc=Functions(robot)
fuc.start()
    

def functionSelect(command_input, response):
    global direction_command, steady
    if 'findColor' == command_input:
        if OLED_connection:
            screen.screen_show(4,'FindColor')
        flask_app.modeselect('findColor')
        flask_app.modeselectApp('APP')

    elif 'motionGet' == command_input:
        if OLED_connection:
            screen.screen_show(4,'MotionGet')
        flask_app.modeselect('watchDog')

    elif 'stopCV' == command_input:
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')
        flask_app.modeselect('none')
        time.sleep(0.5)
        # robot.command_input('stand')
        robot.init_all()

    elif 'fast' == command_input:
        robot.command_input(command_input)

    elif 'slow' == command_input:
        robot.command_input(command_input)

    elif 'police' == command_input:
        if OLED_connection:
            screen.screen_show(4,'POLICE')
        ws2812.police()

    elif 'policeOff' == command_input:
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')
        ws2812.breath(70,70,255)

    elif 'steadyCamera' == command_input:
        if OLED_connection:
            screen.screen_show(4,'steady')
        robot.command_input(command_input)
        steady = 1

    elif 'steadyCameraOff' == command_input:
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')
        robot.command_input(command_input)
        steady = 0

    elif 'Buzzer_Music' == command_input:
        player.start_playing()

    elif 'Buzzer_Music_Off' == command_input:
        player.pause()

def switchCtrl(command_input, response):
    if 'Switch_1_on' in command_input:
        switch.switch(1,1)

    elif 'Switch_1_off' in command_input:
        switch.switch(1,0)

    elif 'Switch_2_on' in command_input:
        switch.switch(2,1)

    elif 'Switch_2_off' in command_input:
        switch.switch(2,0)

    elif 'Switch_3_on' in command_input:
        switch.switch(3,1)

    elif 'Switch_3_off' in command_input:
        switch.switch(3,0) 


def robotCtrl(command_input, response):
    global direction_command
    clen = len(command_input.split())
    if 'forward' in command_input and clen == 2:
        direction_command = 'forward'
        robot.command_input(direction_command)
    
    elif 'backward' in command_input and clen == 2:
        direction_command = 'backward'
        robot.command_input(direction_command)

    elif 'left' in command_input and clen == 2:
        direction_command = 'left'
        robot.command_input(direction_command)

    elif 'right' in command_input and clen == 2:
        direction_command = 'right'
        robot.command_input(direction_command)

    elif 'lookleft' == command_input:
        direction_command = 'lookleft'
        robot.command_input(direction_command)

    elif 'lookright' == command_input:
        direction_command = 'lookright'
        robot.command_input(direction_command)

    elif 'up' == command_input:
        direction_command = 'up'
        robot.command_input(direction_command)

    elif 'down' == command_input:
        direction_command = 'down'
        robot.command_input(direction_command)

    elif 'DTS' in command_input or 'LRStop' in command_input or 'UDstop' in command_input or 'home' == command_input.lower():
        direction_command = 'stand'
        robot.command_input(direction_command)

async def recv_msg(websocket):
    global speed_set,steady

    while True: 
        response = {
            'status' : 'ok',
            'title' : '',
            'data' : None
        }

        data = ''
        data = await websocket.recv()
        try:
            data = json.loads(data)
        except Exception as e:
            print('not A JSON')

        if not data:
            continue

        if isinstance(data,str):
            robotCtrl(data, response)

            switchCtrl(data, response)

            functionSelect(data, response)

            if 'get_info' == data:
                if OLED_connection:
                    vol = batteryMonitor.get_battery_percentage()
                    screen.screen_show(5,f'bat level:{vol}%')
                response['title'] = 'get_info'
                response['data'] = [info.get_cpu_tempfunc(), info.get_cpu_use(), info.get_ram_info(), vol]
            if 'wsB' in data:
                try:
                    set_B=data.split()
                    speed_set = int(set_B[1])
                except:
                    pass

            elif 'CVFL' == data and steady == 0:
                robot.adjust_angle_track_color(13, 1, 20)
                flask_app.modeselect('findlineCV')

            elif 'CVFLColorSet' in data:
                color = int(data.split()[1])
                flask_app.camera.colorSet(color)

            elif 'CVFLL1' in data:
                pos = int(data.split()[1])
                flask_app.camera.linePosSet_1(pos)

            elif 'CVFLL2' in data:
                pos = int(data.split()[1])
                flask_app.camera.linePosSet_2(pos)


        elif(isinstance(data,dict)):
            color = data['data']
            if "title" in data and data['title'] == "findColorSet":
                flask_app.colorFindSetApp(color[0],color[1],color[2])
            elif data['lightMode'] == "breath":  
                ws2812.breath(color[0],color[1],color[2])
            elif data['lightMode'] == "flowing":
                ws2812.flowing(color[0],color[1],color[2])
            elif data['lightMode'] == "rainbow":
                ws2812.rainbow(color[0],color[1],color[2])
            elif data['lightMode'] == "police":
                ws2812.police()


        print(data)
        response = json.dumps(response)
        await websocket.send(response)

async def main_logic(websocket, path):
    await recv_msg(websocket)

def show_wlan0_ip():
    try:
        if OLED_connection:
            result = subprocess.run(
                "ifconfig wlan0 | grep 'inet ' | awk '{print $2}'",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8'
            ) 
            screen.screen_show(2, "IP:" + result.stdout.strip())
    except Exception as e:
        pass

def show_network_mode():
    try:
        if OLED_connection:
            result = subprocess.run(
                "if iw dev wlan0 link | grep -q 'Connected'; then echo 'Station Mode'; else echo 'AP Mode'; fi",
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8'
            )
            screen.screen_show(3, result.stdout.strip())
    except Exception as e:
        pass

if __name__ == '__main__':
    switch.switchSetup()
    switch.set_all_switch_off()
    
    show_wlan0_ip()
    time.sleep(0.5)
    show_network_mode()

    global flask_app
    flask_app = app.webapp()
    flask_app.startthread()

    try:
        ws2812=robotLight.Adeept_SPI_LedPixel(16, 255)
        if ws2812.check_spi_state() != 0:
            ws2812.start()
            ws2812.breath(70,70,255)
        else:
            ws2812.led_close()
    except  KeyboardInterrupt:
        ws2812.led_close()
        pass

    while  1:
        try:				  #Start server,waiting for client
            start_server = websockets.serve(main_logic, '0.0.0.0', 8888)
            asyncio.get_event_loop().run_until_complete(start_server)
            print('waiting for connection...')
            break
        except Exception as e:
            print(e)
            ws2812.set_all_led_color_data(0,0,0)
            ws2812.show()

        try:
            ws2812.set_all_led_color_data(0,80,255)
            ws2812.show()
        except:
            pass
    try:
        asyncio.get_event_loop().run_forever()
    except Exception as e:
        print(e)
        ws2812.set_all_led_color_data(0,0,0)
        ws2812.show()
        robot.cleanup()
