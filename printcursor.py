# -*- coding: utf-8 -*-
"""
Created on Thu Nov 19 22:16:22 2020

@author: Seb
"""
import win32gui
import threading

xlength = 1920
ylength = 1080

# margin
m = 0.2 

leftbound = m * xlength
rightbound = (1 - m) * xlength
upbound = m * ylength
downbound = (1 - m) * ylength

def printit():
  threading.Timer(2.0, printit).start()
  pos = win32gui.GetCursorPos()
  x = pos[0]
  y = pos[1]

  if (x > rightbound and (upbound <= y <= downbound)):
    print("RIGHT")
  elif (x < leftbound and (upbound <= y <= downbound)):
    print("LEFT")
  elif (y > downbound and (leftbound <= x <= rightbound)):
    print("DOWN")
  elif (y < upbound and (leftbound <= x <= rightbound)):
    print("UP")
  else: 
    print("NOT CARDINAL DIRECTION")


printit()