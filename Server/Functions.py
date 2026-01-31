#!/usr/bin/env python3
# File name   : functions.py
# Description : Control Functions
# Author	  : Adeept
# Date		  : 2025/03/12
import time
import threading
import Ultra as ultra
from Move import RaspClaws

class Functions(threading.Thread):
	def __init__(self, robot, *args, **kwargs):
		self.functionMode = 'none'
		self.robot = robot
		self.keep_dist = 30
		self.automatic_min_dist = 20
		self.automatic_max_dist = 40

		super(Functions, self).__init__(*args, **kwargs)
		self.__flag = threading.Event()
		self.__flag.clear()

	def pause(self):
		self.robot.command_input('DTS')
		self.robot.command_input('stand')
		self.functionMode = 'none'
		self.__flag.clear()


	def resume(self):
		self.__flag.set()

	def automatic(self):
		self.functionMode = 'Automatic'
		self.resume()

	def keepDistance(self):
		self.functionMode = 'keepDistance'
		self.resume()

	def distRedress(self): 
		mark = 0
		distValue = ultra.checkdist()
		while True:
			distValue = ultra.checkdist()
			if distValue > 900:
				mark +=  1
			elif mark > 5 or distValue < 900:
					break
			print(distValue)
		return round(distValue,2)

	def automaticProcessing(self):		
		dist = self.distRedress()
		if dist >= self.automatic_max_dist:
			self.robot.command_input("forward")
			time.sleep(2)
		elif dist > self.automatic_min_dist and dist < self.automatic_max_dist:	
			self.robot.command_input('stand')
			self.robot.adjust_init_angle(14, 1, 45)
			# self.robot.set_servo_angle(14, 135)
			time.sleep(0.3)
			distLeft = self.distRedress()

			# self.robot.set_servo_angle(14, 45)
			self.robot.adjust_init_angle(14, -1, 90)
			time.sleep(0.3)
			distRight = self.distRedress()
			# self.robot.set_servo_angle(14, 90)
			self.robot.adjust_init_angle(14, 1, 45)
            
			print(f"distLeft: {distLeft} distRight:{distRight}")
			if distLeft >= distRight:
				self.robot.command_input("left")
				time.sleep(2)
			else:
				self.robot.command_input("right")
				time.sleep(2)
		else:
			self.robot.command_input("backward")
			time.sleep(2)


	def keepDisProcessing(self):
		distanceGet = self.distRedress()
		if distanceGet >= self.keep_dist:
			self.robot.command_input("forward")
		else:
			self.robot.command_input("backward")
		time.sleep(2)


	def functionGoing(self):
		if self.functionMode == 'none':
			self.pause()
		elif self.functionMode == 'Automatic':
			self.automaticProcessing()
		elif self.functionMode == 'keepDistance':
			self.keepDisProcessing()


	def run(self):
		while 1:
			self.__flag.wait()
			self.functionGoing()


if __name__ == '__main__':
	try:
		robot = RaspClaws()
		robot.start()
		# robot.command_input("forward")
		fuc=Functions(robot)
		fuc.start()
		fuc.automatic()
		time.sleep(5)
		fuc.pause()
		# fuc.keepDistance()
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		pass
