#!/usr/bin/env/python
# File name   : server.py
# Description : main programe for RaspClaws
# Website     : www.adeept.com
# E-mail      : support@adeept.com
# Author      : William
# Date        : 2018/08/22

import socket
import time
import threading
from Move import RaspClaws
import os
import FPV
import psutil
import Switch as switch
import RobotLight as robotLight
import ast
import subprocess
import Voltage




steadyMode = 0

def get_cpu_tempfunc():
    """ Return CPU temperature """
    result = 0
    mypath = "/sys/class/thermal/thermal_zone0/temp"
    with open(mypath, 'r') as mytmpfile:
        for line in mytmpfile:
            result = line

    result = float(result)/1000
    result = round(result, 1)
    return str(result)


def get_gpu_tempfunc():
    """ Return GPU temperature as a character string"""
    res = os.popen('/opt/vc/bin/vcgencmd measure_temp').readline()
    return res.replace("temp=", "")


def get_cpu_use():
    """ Return CPU usage using psutil"""
    cpu_cent = psutil.cpu_percent()
    return str(cpu_cent)


def get_ram_info():
    """ Return RAM usage using psutil """
    ram_cent = psutil.virtual_memory()[2]
    return str(ram_cent)


def get_swap_info():
    """ Return swap memory  usage using psutil """
    swap_cent = psutil.swap_memory()[3]
    return str(swap_cent)


def info_get():
    global cpu_t,cpu_u,gpu_t,ram_info
    while 1:
        cpu_t = get_cpu_tempfunc()
        cpu_u = get_cpu_use()
        ram_info = get_ram_info()
        time.sleep(3)


def info_send_client():
    SERVER_IP = addr[0]
    SERVER_PORT = 2256   #Define port serial 
    SERVER_ADDR = (SERVER_IP, SERVER_PORT)
    Info_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Set connection value for socket
    Info_Socket.connect(SERVER_ADDR)
    print(SERVER_ADDR)
    while 1:
        try:
            Info_Socket.send((get_cpu_tempfunc()+' '+get_cpu_use()+' '+get_ram_info()).encode())
            time.sleep(1)
        except:
            pass


def FPV_thread():
    global fpv
    fpv=FPV.FPV()
    fpv.capture_thread(addr[0])


def run():
    global steadyMode
    info_threading=threading.Thread(target=info_send_client)   #Define a thread for communication
    info_threading.setDaemon(True)                             #'True' means it is a front thread,it would close when the mainloop() closes
    info_threading.start()                                     #Thread starts

    while True: 
        data = ''
        data = str(tcpCliSock.recv(BUFSIZ).decode())
        if not data:
            continue
        elif 'forward' == data or 'backward' == data or 'left' == data or 'right' == data or 'up' == data or 'down' == data or 'lookleft' == data or 'lookright' == data:
            robot.command_input(data)
        elif 'TS' in data or 'DS' in data or 'LRstop' in data or 'UDstop' in data:
            robot.command_input('stand')

        elif 'findColor' ==  data:
            if OLED_connection:
                screen.screen_show(4,'FindColor')
            fpv.FindColor(1)
            tcpCliSock.send(('findColor').encode())

        elif 'motionGet' in data:
            if OLED_connection:
                screen.screen_show(4,'MotionGet')
            fpv.WatchDog(1)
            tcpCliSock.send(('motionGet').encode())

        elif 'stopCV' in data:
            fpv.FindColor(0)
            fpv.WatchDog(0)
            fpv.FindLineMode(0)
            tcpCliSock.send(('stopCV').encode())
            time.sleep(0.5)
            robot.init_all()
            if OLED_connection:
                screen.screen_show(4,'FUNCTION OFF')

        elif 'steadyCamera' == data:
            if OLED_connection:
                screen.screen_show(4,'steady')
            robot.command_input(data)
            steadyMode = 1
            tcpCliSock.send(('steadyCamera').encode())
        elif 'steadyCameraOff' == data:
            if OLED_connection:
                screen.screen_show(4,'FUNCTION OFF')
            robot.command_input(data)
            steadyMode = 0
            tcpCliSock.send(('steadyCameraOff').encode())

        elif 'fast' in data:
            robot.command_input(data)
            tcpCliSock.send(('fast').encode())

        elif 'slow' in data:
            robot.command_input(data)
            tcpCliSock.send(('slow').encode())
        elif 'police' == data:
            if OLED_connection:
                screen.screen_show(4,'POLICE')
            ws2812.police()
            tcpCliSock.send(('police').encode())

        elif 'policeOff' == data:
            if OLED_connection:
                screen.screen_show(4,'FUNCTION OFF')
            ws2812.breath(70,70,255)
            tcpCliSock.send(('policeOff').encode())

        elif 'Switch_1_on' in data:
            switch.switch(1,1)
            tcpCliSock.send(('Switch_1_on').encode())

        elif 'Switch_1_off' in data:
            switch.switch(1,0)
            tcpCliSock.send(('Switch_1_off').encode())

        elif 'Switch_2_on' in data:
            switch.switch(2,1)
            tcpCliSock.send(('Switch_2_on').encode())

        elif 'Switch_2_off' in data:
            switch.switch(2,0)
            tcpCliSock.send(('Switch_2_off').encode())

        elif 'Switch_3_on' in data:
            switch.switch(3,1)
            tcpCliSock.send(('Switch_3_on').encode())

        elif 'Switch_3_off' in data:
            switch.switch(3,0)
            tcpCliSock.send(('Switch_3_off').encode())

        elif 'CVFL' == data and steadyMode == 0:
            if not FPV.FindLineMode:
                FPV.FindLineMode = 1
                tcpCliSock.send(('CVFL_on').encode())

        elif 'CVFLColorSet 0' ==  data:
            FPV.lineColorSet = 0
            
        elif 'CVFLColorSet 255' ==  data:
            FPV.lineColorSet = 255

        elif 'CVFLL1' in data:
            try:
                set_lip1=data.split()
                lip1_set = int(set_lip1[1])
                FPV.linePos_1 = lip1_set
            except:
                pass

        elif 'CVFLL2' in data:
            try:
                set_lip2=data.split()
                lip2_set = int(set_lip2[1])
                FPV.linePos_2 = lip2_set
            except:
                pass

        elif 'findColorSet' in data:
            try:
                command_dict = ast.literal_eval(data)
                if 'data' in command_dict and len(command_dict['data']) == 3:
                    r, g, b = command_dict['data']
                    fpv.colorFindSet(r, g, b)
                    print(f"color: r={r}, g={g}, b={b}")
            except (SyntaxError, ValueError):
                print("The received string format is incorrect and cannot be parsed.")
        else:
            pass
        print(data)


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
    global robot
    switch.switchSetup()
    switch.set_all_switch_off()

    batteryMonitor = Voltage.BatteryLevelMonitor()
    batteryMonitor.start()

    robot = RaspClaws()
    robot.start()

    try:
        import OLED
        screen = OLED.OLED_ctrl()
        screen.start()
        screen.screen_show(1, 'ADEEPT.COM')
    except:
        OLED_connection = 0
        print('OLED disconnected\n')
        pass

    show_wlan0_ip()
    time.sleep(0.5)
    show_network_mode()


    HOST = ''
    PORT = 10223                              #Define port serial 
    BUFSIZ = 1024                             #Define buffer size
    ADDR = (HOST, PORT)
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
        try:
            tcpSerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpSerSock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            tcpSerSock.bind(ADDR)
            tcpSerSock.listen(5)                      #Start server,waiting for client
            print('waiting for connection...')
            tcpCliSock, addr = tcpSerSock.accept()
            print('...connected from :', addr)

            fps_threading=threading.Thread(target=FPV_thread)         #Define a thread for FPV and OpenCV
            fps_threading.daemon = True                          #'True' means it is a front thread,it would close when the mainloop() closes
            fps_threading.start()                                     #Thread starts
            break
        except:
            pass

    try:
        ws2812.set_all_led_color_data(64,128,255)
        ws2812.show()
    except:
        pass
    run()   

