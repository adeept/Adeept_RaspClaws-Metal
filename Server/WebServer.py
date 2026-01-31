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

steady = 0
OLED_connection = 1

def functionSelect(command_input, response):
    global steady

    if 'findColor' == command_input:
        if OLED_connection:
            screen.screen_show(4,'FindColor')
        flask_app.modeselect('findColor')

    elif 'motionGet' == command_input:
        if OLED_connection:
            screen.screen_show(4,'MotionGet')
        flask_app.modeselect('watchDog')

    elif 'stopCV' == command_input:
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')
        flask_app.modeselect('none')
        time.sleep(0.5)
        robot.init_all()
        # robot.command_input('stand')

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

    elif 'automatic' == command_input:
        if OLED_connection:
            screen.screen_show(4,'Automatic')
        fuc.automatic()
    elif 'automaticOff' == command_input:
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')
        fuc.pause()

    elif 'keepDistance' == command_input:
        if OLED_connection:
            screen.screen_show(4,'KeepDistance')
        fuc.keepDistance()
    elif 'keepDistanceOff' == command_input:
        if OLED_connection:
            screen.screen_show(4,'FUNCTION OFF')
        fuc.pause()

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
    if 'TS' in command_input or 'DS' in command_input or 'LRstop' in command_input or 'UDstop' in command_input:
        robot.command_input('stand')
    else:
        robot.command_input(command_input)

def configPWM(command_input):
    global steady
    if  steady == 0:
        if 'SiLeft' in command_input:
            servo_index = int(command_input[7:])
            robot.adjust_init_angle(servo_index, 1)
        if 'SiRight' in command_input:
            servo_index = int(command_input[8:])
            robot.adjust_init_angle(servo_index, -1)
        if 'PWMMS' in command_input:
            servo_index = int(command_input[6:])
            robot.persist_Servos_init(servo_index)
        if 'PWMD' in command_input:    
            servo_index = int(command_input[5:])
            robot.init_single_servo(servo_index)

async def check_permit(websocket):
    while True:
        recv_str = await websocket.recv()
        cred_dict = recv_str.split(":")
        if cred_dict[0] == "admin" and cred_dict[1] == "123456":
            response_str = "congratulation, you have connect with server\r\nnow, you can do something else"
            await websocket.send(response_str)
            return True
        else:
            response_str = "sorry, the username or password is wrong, please submit again"
            await websocket.send(response_str)

async def recv_msg(websocket):
    global speed_set, modeSelect,steady

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

            configPWM(data)

            if 'get_info' == data:
                response['title'] = 'get_info'
                response['data'] = [info.get_cpu_tempfunc(), info.get_cpu_use(), info.get_ram_info()]
                if OLED_connection:
                    vol = batteryMonitor.get_battery_percentage()
                    screen.screen_show(5,f'bat level:{vol}%')
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

            elif 'CVFLSP' in data:
                err = int(data.split()[1])
                flask_app.camera.errorSet(err)


        elif(isinstance(data,dict)):
            if data['title'] == "findColorSet":
                color = data['data']
                flask_app.colorFindSet(color[0],color[1],color[2])

        print(data)
        response = json.dumps(response)
        await websocket.send(response)

async def main_logic(websocket, path):
    await check_permit(websocket)
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
    global robot, flask_app
    try:
        import OLED
        screen = OLED.OLED_ctrl()
        screen.start()
        screen.screen_show(1, 'ADEEPT.COM')
    except:
        OLED_connection = 0
        print('OLED disconnected\n')
        pass

    batteryMonitor = Voltage.BatteryLevelMonitor()
    batteryMonitor.start()

    robot = RaspClaws()
    robot.start()

    fuc=Functions(robot)
    fuc.start()

    switch.switchSetup()
    switch.set_all_switch_off()

    show_wlan0_ip()
    time.sleep(0.5)
    show_network_mode()

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
