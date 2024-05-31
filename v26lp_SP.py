#!/usr/bin/env python
#
# v.16
# uses a virtual keypad on screen insted of keyboard
# back to raspberry size and raspbery gpio
# it also will read with a different protocol (i2C)
#
#
#
# v.19 it detect if ti is python 2 or 3
# to start type : sudo python v19.py
#
# Uses turtle graphics for monitoring 
#
# Get rid of autogui
#
#
#
# v.25 is in Spanish and writes data to a file every 10 minutes
#
#
# Hector Gonzalez

#==========================================
# importing libraries
# =========================================


import time
import datetime
import time
import json
import string

import os
import random
import threading 
#import pynput
import sys
import fcntl  
import i2ctest
import csv

sys.path.append('/usr/local/lib/python3.6/site-packages')
sys.path.append('/usr/local/lib/python2.7/dist-packages')
#import pylibftdi

# import pyautogui
# pyautogui is not loger needed
# import '/usr/local/lib/python3.6/site-packages/PyAutoGUI-0.9.48'


if sys.version_info[0] == 3:
    #for Python3                   
    from tkinter import *
    import tkinter as tk
    import tkinter.ttk as ttk
else:
    #for Python2
    import Tkinter as tk
    from Tkinter import *
    import ttk
    import tkMessageBox
  


#                  

#from ttk import *
#from tkinter import ttk
#from tkinter import messagebox





#from pylibftdi.device import Device
#from pylibftdi.driver import FtdiError
#from pylibftdi import Driver
from os import system, name
from time import sleep
from datetime import datetime
import fcntl

import string
'''from AtlasI2C import (
	 AtlasI2C
)'''


''' v14 modules '''
import turtle
from turtle import *
global t1



#!/usr/bin/python

import io
import sys
import fcntl
import time
import copy
import string


class AtlasI2C:

    # the timeout needed to query readings and calibrations
    # LONG_TIMEOUT = 1.5  ** ORIGINAL TIME **
    LONG_TIMEOUT = 7.5
    # timeout for regular commands
    SHORT_TIMEOUT = .3
    # the default bus for I2C on the newer Raspberry Pis, 
    # certain older boards use bus 0
    DEFAULT_BUS = 1
    # the default address for the sensor
    DEFAULT_ADDRESS = 98
    LONG_TIMEOUT_COMMANDS = ("R", "CAL")
    SLEEP_COMMANDS = ("SLEEP", )

    def __init__(self, address=None, moduletype = "", name = "", bus=None):
        '''
        open two file streams, one for reading and one for writing
        the specific I2C channel is selected with bus
        it is usually 1, except for older revisions where its 0
        wb and rb indicate binary read and write
        '''
        self._address = address or self.DEFAULT_ADDRESS
        self.bus = bus or self.DEFAULT_BUS
        self._long_timeout = self.LONG_TIMEOUT
        self._short_timeout = self.SHORT_TIMEOUT
        self.file_read = io.open(file="/dev/i2c-{}".format(self.bus), 
                                 mode="rb", 
                                 buffering=0)
        self.file_write = io.open(file="/dev/i2c-{}".format(self.bus),
                                  mode="wb", 
                                  buffering=0)
        self.set_i2c_address(self._address)
        self._name = name
        self._module = moduletype

	
    @property
    def long_timeout(self):
        return self._long_timeout

    @property
    def short_timeout(self):
        return self._short_timeout

    @property
    def name(self):
        return self._name
        
    @property
    def address(self):
        return self._address
        
    @property
    def moduletype(self):
        return self._module
        
        
    def set_i2c_address(self, addr):
        '''
        set the I2C communications to the slave specified by the address
        the commands for I2C dev using the ioctl functions are specified in
        the i2c-dev.h file from i2c-tools
        '''
        I2C_SLAVE = 0x703
        fcntl.ioctl(self.file_read, I2C_SLAVE, addr)
        fcntl.ioctl(self.file_write, I2C_SLAVE, addr)
        self._address = addr

    def write(self, cmd):
        '''
        appends the null character and sends the string over I2C
        '''
        cmd += "\00"
        self.file_write.write(cmd.encode('latin-1'))

    def handle_raspi_glitch(self, response):
        '''
        Change MSB to 0 for all received characters except the first 
        and get a list of characters
        NOTE: having to change the MSB to 0 is a glitch in the raspberry pi, 
        and you shouldn't have to do this!
        '''
        if self.app_using_python_two():
            return list(map(lambda x: chr(ord(x) & ~0x80), list(response)))
        else:
            return list(map(lambda x: chr(x & ~0x80), list(response[1:])))
            
    def app_using_python_two(self):
        return sys.version_info[0] < 3

    def get_response(self, raw_data):
        if self.app_using_python_two():
            response = [i for i in raw_data if i != '\x00']
        else:
            response = raw_data

        return response

    def response_valid(self, response):
        valid = True
        error_code = None
        if(len(response) > 0):
            
            if self.app_using_python_two():
                error_code = str(ord(response[0]))
            else:
                error_code = str(response[0])
                
            if error_code != '1': #1:
                valid = False

        return valid, error_code

    def get_device_info(self):
        if(self._name == ""):
            return self._module + " " + str(self.address)
        else:
            return self._module + " " + str(self.address) + " " + self._name
        
    def read(self, num_of_bytes=31):
        '''
        reads a specified number of bytes from I2C, then parses and displays the result
        '''
        
        raw_data = self.file_read.read(num_of_bytes)
        response = self.get_response(raw_data=raw_data)
        #print(response)
        is_valid, error_code = self.response_valid(response=response)

        if is_valid:
            char_list = self.handle_raspi_glitch(response[1:])
            result = "Success " + self.get_device_info() + ": " +  str(''.join(char_list))
            #result = "Success: " +  str(''.join(char_list))
        else:
            result = "Error " + self.get_device_info() + ": " + error_code

        return result

    def get_command_timeout(self, command):
        timeout = None
        if command.upper().startswith(self.LONG_TIMEOUT_COMMANDS):
            timeout = self._long_timeout
        elif not command.upper().startswith(self.SLEEP_COMMANDS):
            timeout = self.short_timeout

        return timeout

    def query(self, command):
        '''
        write a command to the board, wait the correct timeout, 
        and read the response
        '''
        self.write(command)
        current_timeout = self.get_command_timeout(command=command)
        if not current_timeout:
            return "sleep mode"
        else:
            time.sleep(current_timeout)
            return self.read()

    def close(self):
        self.file_read.close()
        self.file_write.close()

    def list_i2c_devices(self):
        '''
        save the current address so we can restore it after
        '''
        prev_addr = copy.deepcopy(self._address)
        i2c_devices = []
        for i in range(0, 128):
            try:
                self.set_i2c_address(i)
                self.read(1)
                i2c_devices.append(i)
            except IOError:
                pass
        # restore the address we were using
        self.set_i2c_address(prev_addr)

        return i2c_devices



# =========================================================
#  GPIO This section set the GPIO ports for the Rasbery PI 
#==========================================================

import RPi.GPIO as GPIO
#import RPI.GPIO as GPIO

# RPi GPIO pins used
temp_pin = 22
pH_pin = 23
DOx_pin = 24

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(temp_pin,GPIO.OUT)
GPIO.setup(pH_pin,GPIO.OUT)
GPIO.setup(DOx_pin,GPIO.OUT)

GPIO.output(temp_pin,GPIO.LOW)
GPIO.output(pH_pin,GPIO.LOW)
GPIO.output(DOx_pin,GPIO.LOW)
#===========
# GPIO END
#===========


#===================================
# Global variables
#===================================
global PH_low_p 
global PH_high_p

global DO_low_p 
global DO_high_p

global TMP_low_p
global TMP_high_p

global dev
global devices
global cnt_all
global reading  
   

global min_temp
global max_temp

global min_ph
global max_pm

global min_do
global max_do

global flag_do
global flag_ph
global flag_temp
    
global delay_readings
global color1
global color2
global color3
    

global r_temp 
global r_dox 
global r_ph 


global temp_string

global test_mode
global delete_buttons
global titles
global current_time
global counter01
global delaytime
global window
global exit_loop

# variable to write to usb
global write_header
global write_data
global last_saved_csv
write_header = True
write_data = True
last_saved_csv = 0
# last_saved_csv is a global variable that will contain a value in seconds of the las time saved
# in the following format H * 60 *60 + m *60 +s = total seconds


exit_loop = False
delaytime = 2
flag_ph = False
flag_do = False
flag_temp = False


titles =["zero","Temp Baja","Temp Alta", "DO Bajo","DO Alto","pH Bajo", "pH Alto", "Update delay"] 
valid_digits =['0','1','2','3','4','5','6','7','8','9','.']
valid_keys =['d','c','x', 'e']
#counter01 = 0
test_mode = False #############
delete_buttons = True

min_temp = 0
max_temp = 60
min_do = 0 
max_do = 20
min_ph = 0
max_ph = 14

# restore_files()    
#PH_low_p = min_ph
#PH_high_p = max_ph
#DO_low_p = min_do
#DO_high_p = max_do
#TMP_low_p  = min_temp
#TMP_high_p = max_temp
    
r_temp = 0.00
r_dox = 0.00
r_ph = 0.00
reading = 0.00

#===========================
# COLORS #
#===========================

color1 = '#7575a3'
#color1 = '#71677C'

color2 ='#9f9fdf'
#color2 = '#62466B'

#color3 = '#ff751a'
color3 =  '#F46036'

#==========================
nocolor = 'white'
width01 ='30'  #
height01 ='1'
width02 ='18'
height02 ='1'
width03 ='10'
height03 ='1' 
padx01 =1
pady01=1
padx02 =1
pady02=1
delay_readings = 1

#os.system('bash gpio_create.sh') use only for Atomic py
#os.system('bash gpio_off.sh')


#=========================================
# These functions turn relays ON or OFF
# Optional functions to test them manually
#=========================================
def turn_temp_on():
    global flag_temp
    if flag_temp == True:              
        '''#print('')'''
    else:
        '''print('')'''
        #with open('/sys/class/gpio/gpio329/value', 'w') as f:
        #    f.write("1")
        GPIO.output(temp_pin,GPIO.HIGH)
        flag_temp = True
    update_pump_status()
    return                

         
def turn_temp_off():
    global flag_temp
    if flag_temp == False:
        '''print('Temp relay is already off')'''
    else:
        '''print('Turning temp relay off')  '''
        GPIO.output(temp_pin,GPIO.LOW)
        #with open('/sys/class/gpio/gpio329/value', 'w') as f:
        #    f.write("0") 
        flag_temp = False
    update_pump_status()
    return


def turn_do_on():
    global flag_do
    if flag_do == True:
        '''print('Do relay is already on')'''
    else:
        '''print('Turning DO relay on')'''
        #used with raspberry
        GPIO.output(DOx_pin,GPIO.HIGH)
        #used with Atomic pi
        #with open('/sys/class/gpio/gpio336/value', 'w') as f:
        #    f.write("1")
        flag_do = True
    update_pump_status()
    return
      
def turn_do_off():
    global flag_do
    if flag_do == False:
        '''print('Do relay is already off')'''
    else:
        '''print('Turning DO relay off')          '''
        GPIO.output(DOx_pin,GPIO.LOW)
        #with open('/sys/class/gpio/gpio336/value', 'w') as f:
        #    f.write("0")
        flag_do = False
    update_pump_status()
    return     
      
def turn_ph_on():
    global flag_ph
    if flag_ph == True:
        '''print('ph relay is already on')'''
    else:    
        '''print('Turning PH relay on')'''
        GPIO.output(pH_pin,GPIO.HIGH)
        #with open('/sys/class/gpio/gpio330/value', 'w') as f:
        #    f.write("1")        
        flag_ph = True
    update_pump_status()
    return

def turn_ph_off():
    global flag_ph
    if flag_ph == False:
        '''print('ph relay is already off')'''
    else:
        '''print('Turning PH relay off')'''
        GPIO.output(pH_pin,GPIO.LOW)
        #with open('/sys/class/gpio/gpio330/value', 'w') as f:
        #    f.write("0")
        flag_ph = False
    update_pump_status()
    return    

def test_temp_pump():       
    global flag_temp
    if flag_temp == False:
        turn_temp_on()
    else:
        turn_temp_off()
    update_pump_status()  
    return           
        
def test_do_pump():   
     global flag_do
     if flag_do == False:
        turn_do_on()
     else:
        turn_do_off()
     update_pump_status()  
     return      

def test_ph_pump():   
     global flag_ph
     if flag_ph == False:
        turn_ph_on()
     else:
         turn_ph_off()
     update_pump_status()
     return       

#=================================
# End of pump (relay) functions
#=================================


#===============================
# Functions for  Pane Window 2
#===============================
def update_readings():
        # This function will update the readings on Window pane 3
        global r_temp
        global r_dox
        global r_ph        
        height01 = 1
        width01 = 46
        label_1=Label(frame2, text = 'Temperatura' ,width =width01, height =height01, bg = color1)          
        label_2=Label(frame2, text = str(r_temp),width =width01, height =height01, bg = color1)
        label_3=Label(frame2, text = 'Oxigeno (DO) ' ,  width =width01, height = height01, bg = color2)
        label_4=Label(frame2, text = str(r_dox) ,width =width01, height =height01, bg = color2)
        label_5=Label(frame2, text = 'pH' ,  width =width01, height =height01, bg = color3)
        label_6=Label(frame2, text = str(r_ph),width =width01, height = height01, bg = color3)
        progressbartemp = ttk.Progressbar(frame2, orient = HORIZONTAL, length = 400)
        progressbartemp.config (mode ='determinate', maximum = TMP_high_p, value =  r_temp)
        progressbardo = ttk.Progressbar(frame2, orient = HORIZONTAL, length = 400)
        progressbardo.config (mode ='determinate', maximum = DO_high_p, value =  r_dox)         
        progressbarph = ttk.Progressbar(frame2, orient = HORIZONTAL, length = 400)
        progressbarph.config (mode ='determinate', maximum = PH_high_p, value =  r_ph)
        # Font type and size
        label_1.config(font=("Times New Roman", 14))
        label_2.config(font=("Times New Roman", 14))
        label_3.config(font=("Times New Roman", 14))
        label_4.config(font=("Times New Roman", 14))   
        label_5.config(font=("Times New Roman", 14))    
        label_6.config(font=("Times New Roman", 14))
        # Font color
        label_1.config(foreground ='white')
        label_2.config(foreground ='white')
        label_3.config(foreground ='white')
        label_4.config(foreground ='white')   
        label_5.config(foreground ='white')    
        label_6.config(foreground ='white')
        # padx and pady
        pady01 = 2
        padx01 = 2
        pady02 = 1
        padx02 = 1
        label_1.grid(row=0, column=0,padx =padx01,pady= pady01)
        label_2.grid(row=1, column=0,padx =padx01,pady= pady01)
        label_3.grid(row=0, column=1,padx =padx01,pady= pady01)
        label_4.grid(row=1, column=1,padx =padx01,pady= pady01)
        label_5.grid(row=0, column=2,padx =padx01,pady= pady01)
        label_6.grid(row=1, column=2,padx =padx01,pady= pady01)
        progressbartemp.grid(row=2, column =0,padx =padx02,pady= pady02)
        progressbardo.grid(row=2, column =1,padx =padx02,pady= pady02)
        progressbarph.grid(row=2, column =2,padx =padx02,pady= pady02)
        return
        
def update_bars():
        # This function updates the progress bars on window pane # 2
        global r_temp
        global r_dox
        global r_ph
        global TMP_high_p
        global DO_high_p
        global PH_high_p
        s = ttk.Style()
        s.theme_use('clam')
        s.configure("red.Horizontal.TProgressbar", foreground='red', background='#1aff1a')
        ttk.Progressbar(frame2, style="red.Horizontal.TProgressbar", orient="horizontal", length= 400,mode="determinate", maximum=TMP_high_p, value=r_temp).grid(row=2, column=0)
        ttk.Progressbar(frame2, style="red.Horizontal.TProgressbar", orient="horizontal", length= 400,mode="determinate", maximum=DO_high_p, value=r_dox).grid(row=2, column=1)
        ttk.Progressbar(frame2, style="red.Horizontal.TProgressbar", orient="horizontal", length= 400,mode="determinate", maximum=PH_high_p, value=r_ph).grid(row=2, column=2)
        return
  


#========================================
# Functions for Pane Window 3 high - low
#========================================

def initial_frame3():
        global PH_low_p 
        global PH_high_p
        global DO_low_p 
        global DO_high_p
        global TMP_low_p
        global TMP_high_p
        width03 = 29
        height03 = 1
        label_1=Label(frame3, text = 'Temp Baja' ,width =width03, height = height03 , bg = color1)          
        label_2=Label(frame3, text = str(TMP_low_p),width =width03, height = height03, bg = color1)
        label_3=Label(frame3, text = 'DO Bajo' ,  width =width03, height = height03, bg = color2)
        label_4=Label(frame3, text = str(DO_low_p) ,width =width03, height = height03, bg = color2)
        label_5=Label(frame3, text = 'pH Bajo' ,  width =width03, height = height03, bg = color3)
        label_6=Label(frame3, text = str(PH_low_p),width =width03, height = height03, bg = color3)
        label_7=Label(frame3, text = 'Temp Alta' ,width =width03, height = height03, bg = color1)          
        label_8=Label(frame3, text = str(TMP_high_p),width =width03, height =  height03, bg = color1)
        label_9=Label(frame3, text = 'DO Alta' ,  width =width03, height = height03, bg = color2)
        label_10=Label(frame3, text = str(DO_high_p) ,width =width03, height =  height03, bg = color2)
        label_11=Label(frame3, text = 'pH Alta' ,  width =width03, height = height03, bg = color3)
        label_12=Label(frame3, text = str(PH_high_p),width =width03, height = height03, bg = color3)

        # Font and size
        label_1.config(font=("Times New Roman", 10))
        label_2.config(font=("Times New Roman", 10))
        label_3.config(font=("Times New Roman", 10))
        label_4.config(font=("Times New Roman", 10))   
        label_5.config(font=("Times New Roman", 10))    
        label_6.config(font=("Times New Roman", 10))
        label_7.config(font=("Times New Roman", 10))
        label_8.config(font=("Times New Roman", 10))
        label_9.config(font=("Times New Roman", 10))
        label_10.config(font=("Times New Roman", 10))   
        label_11.config(font=("Times New Roman", 10))    
        label_12.config(font=("Times New Roman", 10))
        
        # font foreground
        label_1.config(foreground ='white')
        label_2.config(foreground ='white')
        label_3.config(foreground ='white')
        label_4.config(foreground ='white')   
        label_5.config(foreground ='white')    
        label_6.config(foreground ='white')
        label_7.config(foreground ='white')
        label_8.config(foreground ='white')
        label_9.config(foreground ='white')
        label_10.config(foreground ='white')   
        label_11.config(foreground ='white')
        label_12.config(foreground ='white')
        padx03 = 2
        pady03 = 1
        # position   
        label_1.grid(row=0, column=0,padx=padx03,pady= pady03)
        label_2.grid(row=0, column=1,padx=padx03,pady= pady03)
        label_3.grid(row=0, column=2,padx=padx03,pady= pady03)
        label_4.grid(row=0, column=3,padx=padx03,pady= pady03)
        label_5.grid(row=0, column=4,padx=padx03,pady= pady03)
        label_6.grid(row=0, column=5,padx=padx03,pady= pady03)
        label_7.grid(row=1, column=0,padx=padx03,pady= pady03)
        label_8.grid(row=1, column=1,padx=padx03,pady= pady03)
        label_9.grid(row=1, column=2,padx=padx03,pady= pady03)
        label_10.grid(row=1, column=3,padx=padx03,pady= pady03)
        label_11.grid(row=1, column=4,padx=padx03,pady= pady03)
        label_12.grid(row=1, column=5,padx=padx03,pady= pady03)
        return
# =================== End of panel 3 functions ================


# =======================================
# Functions for panel 4 (update Buttons)
# ====================================== =     

def write_values():
    global PH_low_p 
    global PH_high_p
    global DO_low_p 
    global DO_high_p
    global TMP_low_p
    global TMP_high_p    
    x = str(TMP_low_p)+':'+str(TMP_high_p)+':'+ str(DO_low_p)+':'+ str(DO_high_p)+':'+  str(PH_low_p)+':'+str(PH_high_p)         
    with open("./stored_values", 'w') as f:
        f.write(x)
    return


def restore_files():
    global TMP_low_p
    global TMP_high_p

    global DO_low_p 
    global DO_high_p

    global PH_low_p 
    global PH_high_p 
    list=[]    
    content =''
   
    #print('Reading values')    
    with open("/home/pi/st/stored_values", 'r') as f:
        if f.mode == 'r':
            content =    f.read()
    #print ('values read',content)
    
    list =(content.split(":"))        

    TMP_low_p =float(list[0])
    TMP_high_p =float(list[1])
    DO_low_p  = float(list[2])
    DO_high_p = float(list[3])
    PH_low_p =float(list[4])
    PH_high_p =float(list[5])
    update_all()
    return

    
 


def update_buttons(st):
        #from tkinter import *
        #from tkinter import ttk
        #
        #import Tkinter
        #import ttk
        buttontmpl=ttk.Button(frame4, text ="Temp Baja",  command = lambda: get_all_key(1))
        buttontmph=ttk.Button(frame4, text ="Temp Alta", command = lambda: get_all_key(2))
        buttondol=ttk.Button(frame4, text = "DO Bajo",    command = lambda: get_all_key(3))
        buttondoh=ttk.Button(frame4, text = "DO Alto",   command = lambda: get_all_key(4))
        buttonphl=ttk.Button(frame4, text = "pH Bajo ",   command = lambda: get_all_key(5))       
        buttonphh=ttk.Button(frame4, text = "pH Alto",   command = lambda: get_all_key(6))        
        buttonReset=ttk.Button(frame4, text ="Valores por defecto", command = reset_default)
        buttonRestore=ttk.Button(frame4, text ="Recuparar valores almacenados ", command = restore_files)

        buttonSave=ttk.Button(frame4, text ="Almacenar valores", command = write_values)
        button2=ttk.Button(frame7, text ="Monitorear", command = monitor_turtle)       
        button4=ttk.Button(frame7, text ="Terminar Programa", command = end_program)
        button5=ttk.Button(frame7, text ="Calibrar Sensores", command = calibrate)
  

 
             
        ''' Change state to st '''
        buttontmpl.state([st])    
        buttontmph.state([st])    
        buttondol.state([st])     
        buttondoh.state([st])     
        buttonphl.state([st])            
        buttonphh.state([st])            
        buttonReset.state([st])
        buttonRestore.state([st])
        buttonSave.state([st])
        button2.state([st])   
        button4.state([st])
        button5.state([st])

                      
        ''' display buttons on the grid '''
        pady04 =5
        padx04 = 45
        buttontmpl.grid(row=0, column=0, padx=padx04, pady =pady04)
        buttontmph.grid(row=0, column=1, padx=padx04, pady =pady04)        
        buttondol.grid(row=0, column=2, padx=padx04, pady =pady04)
        buttondoh.grid(row=0, column=3, padx=padx04, pady =pady04)        
        buttonphl.grid(row=0, column=4, padx=padx04,pady =pady04)                          
        buttonphh.grid(row=0, column=5, padx=padx04,pady =pady04)
        buttonReset.grid(row=1, column=0, padx=100, pady =1 ,columnspan =2)
        buttonRestore.grid(row=1, column=2, padx=100, pady =1 ,columnspan =2)
        buttonSave.grid(row=1, column=4, padx=100, pady =1 ,columnspan =2)
        button2.grid(row=0, column=1, padx=100, pady =10)    
        button4.grid(row=0, column=4, padx=100, pady =10)
        button5.grid(row=0, column=3, padx=100, pady =10)
        return






     

    
# ==========================================================================
# Functions panel 4 (get all ranges)
# ==========================================================================

#===========================================================================
# Get Temperature Range and Validate
# ==========================================================================
def validate_t_l(a,wtd):
        # This function validates the lower range of the temperature and deletes
        # the capture window once a valid value has been entered
        # wtd is the window to be deleted (What to delete)?
        #
        global TMP_low_p 
        global TMP_high_p          
        global min_temp
        global max_temp
        x = float (TMP_low_p)
        y = float (TMP_high_p)
        value = a
        res = value.replace('.', '',1).isdigit()        
        if res:
             value =float(value)
             if value >= x and  value <= y:
                 #print ('The value has been accepted : ',value, '\n')
                 #messagebox.showinfo(title = 'Value accepted', message = 'The value has been accepted')
                 tkMessageBox.showinfo(title = 'Valor acceptado', message = 'El valor has sido aceptado')
                 TMP_low_p = a  #(value) New Temp_low_p = string  of a
                 # New_TMP_low_p = (value)
                 #update_temp_screen_hl(TMP_low_p,TMP_high_p)
                 update_temp_screen_hl()
                 wtd.destroy()                 
                 
             else:
                 #print ('Enter a number between ', x, 'and ',y)
                 #messagebox.showwarning(title = 'Out of range', message = ('Enter a number between '+str(x)+' and  '+str(y)))
                 tkMessageBox.showwarning(title = 'Fuera de rango', message = ('Entre un numbero entre '+str(x)+' y  '+str(y)))
        else:              
      
                 #print('The value has to be a digit, try again')
                 #messagebox.showwarning(title = 'Digit requred', message ='The value must be a digit, try again')
                 tkMessageBox.showwarning(title = 'Solo Numeros', message ='Debe ser un numbero, intente de nuevo')

def validate_key_captured(a,ts,sw ,wtd):
    # 
    #Validates a key captured and uses the followign codes:
    # 'x' delete the window : wtd
    # 'c' clear the entries from the keyboard - reset the string back to blak
    # 'e' indicates what to validate
    #
    global temp_string   
    
    if a == 'x':
        wtd.destroy()  # cancel, kill the window
        return
    else:
       if a == 'c':        # clear, reset the strign to blank
           temp_string = ''
           ts.configure(text = '')                                                        
           ts.grid(row= 4, column=0, padx = 3, pady =3,columnspan = 3)
           return 
       else:
           if a == 'e':
               if sw == 1:
                   validate_t_l(temp_string,wtd)
               if sw == 2:
                   validate_t_h(temp_string,wtd)
               if sw == 3:
                   validate_do_l(temp_string,wtd)
               if sw == 4:
                   validate_do_h(temp_string,wtd)
               if sw == 5:
                   validate_ph_l(temp_string,wtd)
               if sw == 6:
                   validate_ph_h(temp_string,wtd)
               if sw ==7:
                   validate_delay(temp_string,wtd)
           else:
               temp_string = temp_string +str(a)
               ts.configure(text = temp_string)                                                        
               ts.grid(row= 4, column=0, padx = 1, pady =1,columnspan = 3)
               return                     

       

def get_all_key(sw): 
            # Set the lower  and higher values
            # using a virtual screen keypad
            #
            global temp_string
            global PH_low_p 
            global PH_high_p
            global DO_low_p 
            global DO_high_p
            global TMP_low_p
            global TMP_high_p               
            global min_temp
            global max_temp
            global min_ph
            global max_pm
            global min_do
            global max_do
            global flag_do
            global flag_ph
            global flag_temp               
            global r_temp 
            global r_dox 
            global r_ph
            global delaytime
            #           
            temp_string = ''
            capture = Toplevel(root)
            capture.title(titles[sw])
            # read title from matrix title[i]
                      
                       
            #capture.configure(background='white')
            capture.geometry('500x195+1+1')            
            capture.resizable(False,False)
            win = capture            
            framec =ttk.Frame(capture)
            framec.pack()
            framec.config (height =500, width =170)
            framec.config(relief = SUNKEN)
            framec.config(padding = (1,1))
            if sw == 1:
                # temp low
                label_2 = Label(framec, text ='Entre un nummero entre '+ str(TMP_low_p)+ ' y  '+str(TMP_high_p), width =width01, height =height01, bg = color1)
            if sw == 2:
                # temp high
                label_2 = Label(framec, text ='Entre un numero entre '+ str(TMP_low_p)+ ' y  '+str(TMP_high_p), width =width01, height =height01, bg = color1)
            if sw == 3:
                #do low
                label_2 = Label(framec, text ='Entre un mumero entre '+ str(DO_low_p)+ ' y  '+str(DO_high_p), width =width01, height =height01, bg = color2)
            if sw  == 4:                   
                #do high
                label_2 = Label(framec, text ='Enter un numero entre '+ str(DO_low_p)+ ' y  '+str(DO_high_p), width =width01, height =height01, bg = color2)
            if sw == 5:
                # ph low
                label_2 = Label(framec, text ='Entre un numero entre '+ str(PH_low_p)+ ' y  '+str(PH_high_p), width =width01, height =height01, bg = color3)
            if sw == 6:
                #ph high
                label_2 = Label(framec, text ='Enter un numero entre '+ str(PH_low_p)+ ' y  '+str(PH_high_p), width =width01, height =height01, bg = color3)
                # end of case
            if sw==7:
                #delay time
                label_2 = Label(framec, text ='Entre un numero entre  2 y  60)', width  = width01, height =height01, bg = nocolor)
            #===================================================                   
            # creates the virtual keypad on screen using buttons
            #===================================================
            button00=ttk.Button(framec, text ="0", command = lambda :validate_key_captured('0',entrypad,sw, win))
            button01=ttk.Button(framec, text ="1", command = lambda :validate_key_captured('1',entrypad,sw, win))
            button02=ttk.Button(framec, text ="2", command = lambda :validate_key_captured('2',entrypad,sw, win))
            button03=ttk.Button(framec, text ="3", command = lambda :validate_key_captured('3',entrypad,sw, win))
            button04=ttk.Button(framec, text ="4", command = lambda :validate_key_captured('4',entrypad,sw, win))
            button05=ttk.Button(framec, text ="5", command = lambda :validate_key_captured('5',entrypad,sw, win))
            button06=ttk.Button(framec, text ="6", command = lambda :validate_key_captured('6',entrypad,sw, win))
            button07=ttk.Button(framec, text ="7", command = lambda :validate_key_captured('7',entrypad,sw, win))
            button08=ttk.Button(framec, text ="8", command = lambda :validate_key_captured('8', entrypad,sw,win))
            button09=ttk.Button(framec, text ="9", command = lambda :validate_key_captured('9',entrypad,sw, win))
            button_period=ttk.Button(framec, text =".", command = lambda :validate_key_captured('.',entrypad,sw ,win))
            button_enter=ttk.Button(framec, text ="Entrar", command = lambda :validate_key_captured('e',entrypad,sw, win))            
            button_clr=ttk.Button(framec, text ="Borrar", command = lambda :validate_key_captured('c',entrypad,sw,win))                                     
            button_canx=ttk.Button(framec, text =" Cancelar ", command = lambda :validate_key_captured('x',entrypad,sw,win))
            entrypad = Label(framec, text = temp_string, width =40, height =height01, bg = nocolor)                                                        
          
            button07.grid(row=0,   column=0, padx=1, pady =1)
            button08.grid(row=0,   column=1, padx=1, pady =1)
            button09.grid(row=0,   column=2, padx=1, pady =1)
            button_canx.grid(row=0,  column=3, padx=1, pady =1)                                    

            button04.grid(row=1,    column=0, padx=1, pady =1)                                     
            button05.grid(row=1,    column=1, padx=1, pady =1)                                     
            button06.grid(row=1,    column=2, padx=1, pady =1)
            button_clr.grid(row=1,  column=3, padx=1, pady =1)
            
            button01.grid(row=2,     column=0, padx=1, pady =1)                                     
            button02.grid(row=2,     column=1, padx=1, pady =1)                                     
            button03.grid(row=2,     column=2, padx=1, pady =1)
                                                        
            button00.grid(row=3,      column=0, padx=1, pady =1)
            button_period.grid(row=3, column=1, padx=1, pady =1)
            button_enter.grid(row=3,  column=2, padx=1, pady =1)
             
            
            entrypad.grid(row= 4, column=0, padx = 1, pady =1,columnspan = 3)
            label_2.grid(row=5, column=0,padx = 1, pady =1,columnspan = 3)




def validate_t_h(a,wtd):
        # This function validates the higher range of the temperature and deletes
        # the capture window once a valid value has been entered
        #
        global TMP_low_p 
        global TMP_high_p          
        global min_temp
        global max_temp
        x = float(TMP_low_p)
        y = float(TMP_high_p)    
        value = a
        res = value.replace('.', '',1).isdigit()        
        if res:     
             value =float(value)
             if value >= x and  value <= y:
                 #print ('The value has been accepted : ',value, '\n')
                 #messagebox.showinfo(title = 'Value accepted', message = 'The value has been accepted')
                 tkMessageBox.showinfo(title = 'Volor aceptado', message = 'El valor ha sido aceptado')
                 #TMP_low_p = str(value)
                 TMP_high_p = str(a) # (value2)
                 update_temp_screen_hl() 
                 #update_temp_screen_hl(TMP_low_p,TMP_high_p)                
                 wtd.destroy()                 
                 return ()
             else:
                 #print ('Enter a number between ', x, 'and ',y)
                 #messagebox.showwarning(title = 'Out of range', message = ('Enter a number between '+str(TMP_low_p)+' and  '+str(TMP_high_p)))
                 tkMessageBox.showwarning(title = 'Fuera de rango', message = ('Entre un numero entre '+str(TMP_low_p)+' y  '+str(TMP_high_p))) 
            
        else:
                 #print('The value has to be a digit, try again')
                 #messagebox.showwarning(title = 'Digit required', message ='The value must be a digit, try again')                                  
                 tkMessageBox.showwarning(title = 'Requiere numero', message ='El valor debe ser un numero, Intente de nuevo')


#==========================================================================
# End of temperature Range
#==========================================================================





#===========================================================================
# Get Oxygen Range and Validate
# ==========================================================================


def validate_do_l(a,wtd):
        # This function validates the lower range of the DO and deletes
        # the capture window once a valid value has been entered
        #
        global DO_low_p 
        global DO_high_p          
        global min_do
        global max_do
        x = float (DO_low_p)
        y = float (DO_high_p)
        value = a
        res = value.replace('.', '',1).isdigit()        
        if res:
             value =float(value)
             if value >= x and  value <= y:
                 #print ('The value has been accepted : ',value, '\n')
                 #messagebox.showinfo(title = 'Value accepted', message = 'The value has been accepted')
                 tkMessageBox.showinfo(title = 'Valor aceptado', message = 'El valor ha sido aceptado')
                 DO_low_p = a            
                 update_do_screen_hl()                
                 wtd.destroy()                 
                 
             else:                 
                 #messagebox.showwarning(title = 'Out of range', message = ('Enter a number between '+str(x)+' and  '+str(y)))
                 tkMessageBox.showwarning(title = 'Fuea de Rango', message = ('Entre un number entre '+str(x)+' y  '+str(y)))
        else:            
                     
                 #messagebox.showwarning(title = 'Digit required', message ='The value must be a digit, try again')
                 tkMessageBox.showwarning(title = 'Numero requerido', message ='El valor debe ser un digito, trate de nuevo')


def validate_do_h(a,wtd):
        # This function validates the higher range of the DO and deletes
        # the capture window once a valid value has been entered
        #
        global DO_low_p 
        global DO_high_p          
        global min_do
        global max_do
        x = float(DO_low_p)
        y = float(DO_high_p)    
        value = a
        res = value.replace('.', '',1).isdigit()        
        if res:     
             value =float(value)
             if value >= x and  value <= y:
                 #print ('The value has been accepted : ',value, '\n')
                 #messagebox.showinfo(title = 'Value accepted', message = 'The value has been accepted')
                 tkMessageBox.showinfo(title = 'Value accepted', message = 'The value has been accepted')
                 
                 #TMP_low_p = str(value)
                 DO_high_p = str(a) # (value2)
                 #update_do_screen_hl(DO_low_p,DO_high_p)
                 update_do_screen_hl()    
                 wtd.destroy()                 
                 return ()
             else:
                 #print ('Enter a number between ', x, 'and ',y)
                 #messagebox.showwarning(title = 'Out of range', message = ('Enter a number between '+str(DO_low_p)+' and  '+str(DO_high_p)))
                 tkMessageBox.showwarning(title = 'Fuera de rango', message = ('Entere un number entre '+str(DO_low_p)+' y  '+str(DO_high_p)))
            
        else:
                 #print('The value has to be a digit, try again')
                 #messagebox.showwarning(title = 'Digit requred', message ='The value must be a digit, try again')
                 tkMessageBox.showwarning(title = 'Numero requerido', message ='El valor debe ser un digito, trate de nuevo')  
         
#====================================================================
# End of Oxygen Range
#====================================================================




#===========================================================================
# Get PH Range and Validate
# ==========================================================================
def validate_ph_l(a,wtd):
        # This function validates the lower range of the DO and deletes
        # the capture window once a valid value has been entered
        #
        global PH_low_p 
        global PH_high_p          
        global min_ph
        global max_ph
        x = float (PH_low_p)
        y = float (PH_high_p)
        value = a
        res = value.replace('.', '',1).isdigit()        
        if res:
             value =float(value)
             if value >= x and  value <= y:
                 #print ('The value has been accepted : ',value, '\n')
                 #messagebox.showinfo(title = 'Value accepted', message = 'The value has been accepted')
                 tkMessageBox.showinfo(title = 'Valor aceptado', message = 'El valor ha sido aceptado')
                 
                 PH_low_p = a  #(value) New Temp_low_p = string  of a
                 # New_TMP_low_p = (value)
                 #update_do_screen_hl(DO_low_p,DO_high_p) 
                 update_ph_screen_hl()                
                 wtd.destroy()                 
                 
             else:
                 #print ('Enter a number between ', x, 'and ',y)
                 #messagebox.showwarning(title = 'Out of range', message = ('Enter a number between '+str(x)+' and  '+str(y)))
                 tkMessageBox.showwarning(title = 'Fuera de rango', message = ('Entre un number entre '+str(x)+' y  '+str(y)))
        else:              
      
                 #print('The value has to be a digit, try again')
                 #messagebox.showwarning(title = 'Digit required', message ='The value must be a digit, try again')
                 tkMessageBox.showwarning(title = 'Numero requrido', message ='El valor debe ser un numero, trate de nuevo')  


def validate_ph_h(a,wtd):
        # This function validates the higher range of the DO and deletes
        # the capture window once a valid value has been entered
        #
        global PH_low_p 
        global PH_high_p          
        global min_ph
        global max_ph
        x = float(PH_low_p)
        y = float(PH_high_p)    
        value = a
        res = value.replace('.', '',1).isdigit()        
        if res:     
             value =float(value)
             if value >= x and  value <= y:
                 #print ('The value has been accepted : ',value, '\n')
                 #messagebox.showinfo(title = 'Value accepted', message = 'The value has been accepted')
                 tkMessageBox.showinfo(title = 'Valor aceptado', message = 'El valro ha sido aceptado')
                 #TMP_low_p = str(value)
                 PH_high_p = str(a) # (value2)
                 #update_do_screen_hl(DO_low_p,DO_high_p)
                 update_ph_screen_hl()    
                 wtd.destroy()                 
                 return ()
             else:
                 #print ('Enter a number between ', x, 'and ',y)
                 #messagebox.showwarning(title = 'Out of range', message = ('Enter a number between '+str(DO_low_p)+' and  '+str(DO_high_p)))
                 tkMessageBox.showwarning(title = 'Fuera de rango', message = ('Enre un numero entre '+str(DO_low_p)+' y  '+str(DO_high_p))) 
            
        else:
                 #print('The value has to be a digit, try again')
                 #messagebox.showwarning(title = 'Digit required', message ='The value must be a digit, try again')                                     
                 tkMessageBox.showwarning(title = 'Numero requrido', message ='El valor debe ser un numero, trate de nuevo')    
#====================================================================
# End of pH Range
#====================================================================



def validate_delay(a,wtd):
        # This function validates the higher range of the DO and deletes
        # the capture window once a valid value has been entered
        #
        global delaytime
        x = 2
        y = 60    
        value = a
        res = value.replace('.', '',1).isdigit()        
        if res:     
             value =float(value)
             if value >= x and  value <= y:
                 #print ('The value has been accepted : ',value, '\n')
                 #messagebox.showinfo(title = 'Value accepted', message = 'The value has been accepted')
                 tkMmessageBox.showinfo(title = 'Valor aceptado', message = 'El valor has sido aceptado')
                 #TMP_low_p = str(value)
                 delaytime = int(a) # (value2)
                 #update_do_screen_hl(DO_low_p,DO_high_p)
                 #update_ph_screen_hl()    
                 wtd.destroy()                 
                 return ()
             else:
                 #print ('Enter a number between ', x, 'and ',y)
                 #messagebox.showwarning(title = 'Out of range', message = 'Enter a number between 2 and 60')
                 tkMessageBox.showwarning(title = 'Fuera de rango', message = 'Entre un numero entre 2 y 60')
        else:
                 #print('The value has to be a digit, try again')
                 #messagebox.showwarning(title = 'Digit required', message ='The value must be a digit, try again')  
                 tkMessageBox.showwarning(title = 'Numero requrido', message ='El valor debe ser un digito, trate de nuevo') 








#========================================
# Functions for pane window 3 Low - High
#========================================
       
def update_temp_screen_hl():
    # Display Temperature low and high    
    global TMP_low_p 
    global TMP_high_p  
    a = TMP_low_p 
    b = TMP_high_p
    height03 = 1
    width03 = 29
    label_2=Label(frame3, text = str(a),width =width03, height = height03, bg = color1)
    label_8=Label(frame3, text = str(b) ,width =width03, height = height03, bg = color1)
    label_2.config(font=("Times New Roman", 10))
    label_8.config(font=("Times New Roman", 10))
    label_2.config(foreground ='white')   
    label_8.config(foreground ='white')   
    label_2.grid(row=0, column=1,padx=padx02,pady= pady02)   
    label_8.grid(row=1, column=1,padx=padx02,pady= pady02)
    return

def update_do_screen_hl():
    # Display DO low and high    
    global DO_low_p 
    global DO_high_p
    a = DO_low_p
    b = DO_high_p
    height03 = 1
    width03 = 29
    label_4=Label(frame3, text = str(a),width =width03, height = height03, bg = color2)
    label_10=Label(frame3, text = str(b) ,width =width03, height = height03, bg = color2)
    label_4.config(font=("Times New Roman", 10))
    label_10.config(font=("Times New Roman", 10))
    label_4.config(foreground ='white')   
    label_10.config(foreground ='white')   
    label_4.grid(row=0, column=3,padx=padx02,pady= pady02)   
    label_10.grid(row=1, column=3,padx=padx02,pady= pady02)
    return          

def update_ph_screen_hl():
    # Display ph low and high    
    global PH_low_p  
    global PH_high_p
    height03 = 1
    width03 = 29
    a = PH_low_p  
    b = PH_high_p
    label_6=Label(frame3, text = str(a),width =width03, height = height03, bg = color3)
    label_12=Label(frame3, text = str(b) ,width =width03, height = height03, bg = color3)
    label_6.config(font=("Times New Roman", 10))
    label_12.config(font=("Times New Roman", 10))
    label_6.config(foreground ='white')   
    label_12.config(foreground ='white')   
    label_6.grid(row=0, column=5,padx=padx02,pady= pady02)   
    label_12.grid(row=1, column=5,padx=padx02,pady= pady02)
    return       

def reset_default():    
    # This function reset all the range values to the default.
    global TMP_low_p 
    global TMP_high_p
    global DO_low_p 
    global DO_high_p
    global PH_low_p  
    global PH_high_p   
    global min_temp
    global max_temp
    global min_do 
    global max_do
    global min_ph
    global max_ph
    global r_temp 
    global r_dox 
    global r_ph 
    min_temp = 0
    max_temp = 60
    min_do = 0 
    max_do = 20
    min_ph = 0
    max_ph = 14
    TMP_low_p  = min_temp
    TMP_high_p = max_temp    
    DO_low_p  =min_do
    DO_high_p = max_do
    PH_low_p  = min_ph
    PH_high_p = max_ph
    update_temp_screen_hl()
    update_do_screen_hl()
    update_ph_screen_hl()
    return

# ======================================
# Pane Window 5 empty
# ======================================


      
# =================================
# Pane Window 6 state of the pumps 
# =================================
def initial_pumps():
    height06 =1
    width06= 23
    #frame6 = ttk.Frame(panedwindow, width =100, height =130, relief = SUNKEN)
    label_1=Label(frame6, text = 'Bomba de Temperatura esta: ' ,width =width06, height =height06, bg = color1)          
    label_2=Label(frame6, text = 'Bomba de Oxygen      esta: ',width =width06, height =height06, bg = color2)
    label_3=Label(frame6, text = 'Bomba de pH pump     esta:     ' ,  width =width06, height = height06, bg = color3)       
    label_4=Label(frame6, text = '' ,width =width06, height =height06, bg = nocolor)          
    label_5=Label(frame6, text = '',width =width06, height =height06, bg = nocolor)
    label_6=Label(frame6, text = '' ,  width =width06, height = height06, bg = nocolor)
    if flag_temp == False:
            label_4.config(text= 'apagada')
            label_4.config(foreground = 'red')
    else:       
            Label4.config(text='funcionando')
            Label4.config(foreground = 'green')

    if flag_do == False:
            label_5.config(text= 'apagada')
            label_5.config(foreground = 'red')
    else:       
            Label5.config(text='funcionando')
            Label5.config(foreground = 'green')
         
    if flag_ph == False:
            label_6.config(text= 'apagada')
            label_6.config(foreground = 'red')
    else:       
            Label_6.config(text='funcionando')
            Label_6.config(foreground = 'green')          
    padx06 = 2
    pady06 = 1
    label_1.grid(row=0, column=1,padx =padx06,pady= pady06)
    label_4.grid(row=0, column=2,padx =padx06,pady= pady06)
    label_2.grid(row=0, column=3,padx =padx06,pady= pady06)
    label_5.grid(row=0, column=4,padx =padx06,pady= pady06)
    label_3.grid(row=0, column=5,padx =padx06,pady= pady06) 
    label_6.grid(row=0, column=6,padx =padx06,pady= pady06)
    return

#==============================
# update the state of the pumps
#==============================
def update_pump_status():
    global flag_temp
    global flag_do
    global flag_ph   
    width06 = 10
    height06 = 1
    label_4=Label(frame6, text = '' ,width =width06, height =height06, bg = nocolor)          
    label_5=Label(frame6, text = '',width =width06, height =height06, bg = nocolor)
    label_6=Label(frame6, text = '' ,  width =width06, height = height06, bg = nocolor)
    if flag_temp == False:
        label_4.config(text= 'off')
        label_4.config(foreground = 'red')
    else:       
        label_4.config(text='on')
        label_4.config(foreground = 'green')

    if flag_do == False:
        label_5.config(text= 'off')
        label_5.config(foreground = 'red')
    else:       
        label_5.config(text='on')
        label_5.config(foreground = 'green')
     
    if flag_ph == False:
        label_6.config(text= 'off')
        label_6.config(foreground = 'red')
    else:       
        label_6.config(text='on')
        label_6.config(foreground = 'green')             
  
    label_4.grid(row=0, column=2,padx =padx02,pady= pady02)    
    label_5.grid(row=0, column=4,padx =padx02,pady= pady02)    
    label_6.grid(row=0, column=6,padx =padx02,pady= pady02)
    return


def calibrate():
    #global window
    #quit_confirm = False
    #quit_confirm = tkMessageBox.askyesno(title ='End program', message ='Desea terminar el programa ?')
    
    #if quit_confirm == True:
    ''' # Turn Relays off and quit the program'''            
    turn_temp_off()
    turn_do_off()
    turn_ph_off()
    kill_turtle()
    #loop_two('')
    root.destroy()
    os.system("python /home/pi/st/cal08_SP.py")
    print ('Exiting the program')
    #window.destroy()        
    sys.exit() 
    #else:    
    return()





    
    pass
  

#===========================================================
# Display initial frame 7  
# Reset values button,  start button, and end program button
#===========================================================
def initial_frame7():
    global TMP_low_p 
    global TMP_high_p
    global DO_low_p 
    global DO_high_p
    global PH_low_p  
    global PH_high_p   
    global min_temp
    global max_temp
    global min_do 
    global max_do
    global min_ph
    global max_ph
    global r_temp 
    global r_dox 
    global r_ph
    
    #b = button=ttk.Button(frame7, text ="Read sensors one time" ,command = lambda : loop_two(b))
    #b.grid(row=0, column=0, padx=100, pady =10)   
    
    button2=ttk.Button(frame7, text ="Monitorear", command = monitor_turtle)
    button2.grid(row=0, column=1, padx=100, pady =10)
    
    button3=ttk.Button(frame7, text ="Parar de Monitorear", command = kill_turtle)
    button3.grid(row=0, column=2, padx=100, pady =10)
        
            
    button5=ttk.Button(frame7, text ="Calibrar Sensores", command = calibrate)
    button5.grid(row=0, column=3, padx=100, pady =10)
    

    button4=ttk.Button(frame7, text ="Terminar Programa", command = end_program)
    button4.grid(row=0, column=4, padx=100, pady =10)


    
    return        

        
def loop_two(b):        
    global TMP_low_p 
    global TMP_high_p
    global DO_low_p
    global DO_high_p
    global PH_low_p  
    global PH_high_p   
    global min_temp
    global max_temp
    global min_do 
    global max_do
    global min_ph
    global max_ph
    global r_temp 
    global r_dox 
    global r_ph
    global delete_buttons
    global counter01
    global delaytime
    display_time()
    '''if delete_buttons == True:
       delete_update_buttons()                       
       delete_buttons = False        
    else:        
       display_update_buttons()      '''
  
    #counter01 =  counter01 +1
    #b.invoke()
    '''print('//////////Counter = ', str(counter01))'''
    #update_all()         
    try:
        start_monitor()        
        '''print ('####### loop  finished  iteration')'''
        #print('### Delay time is:  ',delaytime)      
        update_all()        
        return
    except:
        print(' Exept error')    
        start_monitor()  
        update_all()        
        return               
      
#==========================================
#  End Initial frame 7

  
   
   


#===============================
# Update all
#
def update_all():
    global PH_low_p 
    global PH_high_p
    global DO_low_p 
    global DO_high_p
    global TMP_low_p
    global TMP_high_p
    global dev
    global devices
    global cnt_all
    global reading       
    global min_temp
    global max_temp
    global min_ph
    global max_pm
    global min_do
    global max_do
    global flag_do
    global flag_ph
    global flag_temp        
    global delay_readings
    global color1
    global color2
    global color3        
    global PH_low_p
    global PH_high_p        
    global DO_low_p 
    global DO_high_p        
    global TMP_low_p 
    global TMP_high_p        
    global flag_ph
    global flag_do
    global flag_temp        
    global min_temp 
    global max_temp        
    global min_do  
    global max_do        
    global min_ph 
    global max_ph      
    global r_temp
    global r_dox
    global r_ph
    global second_run    
   
    #display_update_buttons()
    #initial_pumps()
    #initial_frame7()
    
    update_temp_screen_hl()
    update_do_screen_hl()
    update_ph_screen_hl()
    update_readings()
    update_bars()     
    return


#==========================================================
# This functions were taken and addapted from the web site:
# atlas-scientific.com, the manufacturer of th sensors
# =========================================================

''' this modules read from ic2 '''

def print_devices(device_list, device):
    global delaytime
    #delaytime =2
    MyString = ''
    y =''
    for i in device_list:
        if(i == device):
            '''print("--> " + i.get_device_info())'''
        else:
            '''print(" - " + i.get_device_info())'''
    for dev in device_list:
        dev.write("R")
        time.sleep(delaytime)
        for dev in device_list:                
                #print 'This is my dev' , dev
                y= dev.read()
                #print'My read xxxxxxxxxxxxxxxxx',dev.read()
                if y.startswith('Success'):
                    MyString = (MyString +y)               
    #print("This is my string", Mystring)
    return(MyString)

    
def get_devices():
    device = AtlasI2C()
    device_address_list = device.list_i2c_devices()
    device_list = []
    
    for i in device_address_list:
        device.set_i2c_address(i)
        response = device.query("I")
        moduletype = response.split(",")[1] 
        response = device.query("name,?").split(",")[1]
        device_list.append(AtlasI2C(address = i, moduletype = moduletype, name = response))
    return device_list 
       

       
def read_sensors():
        # change this sample code to a functin to read the sensors
        x = ''
        readings =[0]
        device_list = get_devices()            
        device = device_list[0]
        #print_help_text()
        x = print_devices(device_list, device)           
        #print( 'String read: ',x)
        return (x)  # return the string with all values as a function




def start_monitor():
            # global variables
            global r_temp 
            global r_dox 
            global r_ph 
            global reading
            global flag_temp
            global flag_dox
            global flag_ph
            global PH_low_p  
            global PH_high_p
            global DO_low_p 
            global DO_high_p
            global TMP_low_p 
            global TMP_high_p
            global min_temp 
            global max_temp    
            global min_do  
            global max_do    
            global min_ph 
            global max_ph
            global delay_readings            
            x = read_sensors()
            a =x.split(':',3)
            r_dox = float(a[1].lstrip()[0:4])
            r_ph = float(a[2].lstrip()[0:4])
            r_temp = float(a[3].lstrip()[0:5])

            #r_dox = float(a[1].lstrip()[0:3])
            #r_ph = float(a[2].lstrip()[0:3])
            #r_temp = float(a[3].lstrip()[0:3])




            
            '''print ('DO =   ',r_dox)'''
            check_do_pump(r_dox)
            '''print ('pH =   ',r_ph)'''
            check_ph_pump(r_ph)
            '''print ('temp = ', r_temp)'''
            check_temp_pump(r_temp)
            return   
#=======================================================
# End of functions form atlas.scientific.com
#=======================================================  



''' Check pumps'''

def check_temp_pump(x):
    # Check temperature    
    global flag_temp
    global TMP_low_p    
    global TMP_high_p
    a = float(TMP_low_p)
    b =float(TMP_high_p)
    update_all()    
    if (x >= a ) and (x <= b ) and (flag_temp == False):
        if flag_temp == True:   
            '''print ('The reading is within the range. No action is needed')'''
    else:        
        if x < a:            
            #print('The reading is smaller than the minimum range')
            turn_temp_on()
        if x >= b:                     
            #print('The reading is greater or equal than the maximum range')
            turn_temp_off()



def check_do_pump(x):
    # Check do pumps  
    global flag_do
    global DO_low_p 
    global DO_high_p    
    a = float(DO_low_p)
    b = float(DO_high_p)
    update_all()    
    if (x >= a) and (x <= b) and (flag_do == False):
        if flag_do == True:    
            '''print ('The reading is within the range. No action is needed')'''
    else:        
        if x < a:            
            #print('The reading is smaller than the minimum range')
            turn_do_on()
        if x >=  b:                     
            #print('The reading is greater or equal than the maximum range')
            turn_do_off()

            
def check_ph_pump(x):
    # Check do pumps  
    global flag_ph
    global PH_low_p 
    global PH_high_p    
    a = float(PH_low_p)
    b = float(PH_high_p)
    update_all()    
    if (x >= a ) and (x <= b) and (flag_ph == False):     
            '''print ('The reading is within the range. No action is needed')'''
    else:        
        if x < float(PH_low_p):            
            #print('The reading is smaller than the minimum range')
            turn_ph_on()
        if x >=  b:                     
            #print('The reading is greater or equal than the maximum range')
            turn_ph_off()





def end_program():       
        #global window
        quit_confirm = False
        quit_confirm = tkMessageBox.askyesno(title ='End program', message ='Do you want to stop the program')        
        if quit_confirm == True:
            ''' # Turn Relays off and quit the program'''            
            turn_temp_off()
            turn_do_off()
            turn_ph_off()
            kill_turtle()
            write_values() 
            #loop_two('')
            root.destroy()
            print ('Exiting the program')
            #window.destroy()
            sys.exit() 
        else:
            return()

    
def manual_test_pumps():
    '''    module  use for test only '''
    buttontmp=ttk.Button(frame5, text ="Temperatura Relay", command = test_temp_pump)
    buttondo=ttk.Button(frame5, text = "DO relay", command = test_do_pump)
    buttonph=ttk.Button(frame5, text = "pH relay", command = test_ph_pump)
    buttontmp.grid(row=0, column=1, padx=50, pady =1)   
    buttondo.grid(row=0, column=3, padx =50, pady =1)   
    buttonph.grid(row=0, column=6, padx =50,pady =1)
   

def display_time():
    #if the program is in test mode, it display the pumps, otherwise displays time.
    if test_mode == True:
        manual_test_pumps()        
    else:
        #display_time
        now =datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        label_5_1=Label(frame5, text= 'Tiempo de la ultima lectura: '+ dt_string ,width =50, height =height03)          
        label_5_1.grid(row=0, column=0, padx=10, pady =5)
        #########################
        check_csv()
        #########################
        if exit_loop == False:
            ''''Display "Leyendo Sensor if the program is monitoring continuosly '''
            label_5_2=Label(frame5, text= 'Leyendo  Sensoress ...', width =50, height =height03)          
            label_5_2.grid(row=1, column=0, padx=10, pady =5)
            time.sleep(16)
        return     



'''Go ro the starting position x, y used with turtle'''
def go_to(x,y):
    t1.penup()    
    t1.setpos(x,y)
    t1.pendown()


'''display the status of the pumps - used with turtle'''
def display_pump_status():
    draw_rectangle(-600,-260,400,35 ,color1)
    draw_rectangle(-200,-260,400,35 ,color2)
    draw_rectangle( 200,-260,400,35 ,color3)
    '''Display pumps status '''
    display_text(-590,-257,'Temp pump is:','white','Arial',16,'normal')
    display_text(-190,-257,'DO pump is: ','white' ,'Arial',16,'normal')
    display_text(260,-257,'pH Pump is :','white' ,'Arial',16,'normal')
    '''display status of the pumps'''    
    if flag_temp == False: 
        display_text(-420,-257,'Off','red','Arial',18,'bold')           
    else:
        display_text(-420,-257,'On ','green','Arial',18,'bold')
        
    if flag_do == False:
        display_text(0,-257,'Off','red' ,'Arial',18,'bold')           
    else:
        display_text(0,-257,'On ','green' ,'Arial',18,'bold')
        
    if flag_ph == False:
        display_text(450,-257,'Off','red' ,'Arial',18,'bold')       
    else:
        display_text(450,-257,'on','green' ,'Arial',18,'bold')
    return    



''' draw monitoring screen '''

def draw_monitoring_screen():
    '''Draw Rectangles -draw and fillout a
    rectangle paramaters: x, y starting position w, h widht and heigh, c color'''
        
    draw_rectangle(-600,-5,500,20 ,color1)
    draw_rectangle(-200,-5,400,20 ,color2)
    draw_rectangle( 200,-5,300,20 ,color3)  
    
    ''' Temperature '''
    display_text(-580,-3,'Temperatura:','white','Arial',12,'bold')
    
    '''DO'''
    display_text(-180,-3,'DO: ','white' ,'Arial',12,'bold')
    
    '''pH'''
    display_text(220,-3,'pH:','white' ,'Arial',12,'bold')       
    return



''' update values '''
def update_screen_values():
    global r_temp 
    global r_dox 
    global r_ph
    
    global PH_low_p 
    global PH_high_p

    global DO_low_p 
    global DO_high_p

    global TMP_low_p
    global TMP_high_p
    
    global flag_do
    global flag_ph
    global flag_temp
    draw_monitoring_screen() 
    ''' Temperature '''
    display_text(-320,-3,r_temp,'white','Arial',12,'bold')
    
    '''DO'''
    display_text(-95,-3,r_dox,'white' ,'Arial',12,'bold')
    

    '''pH'''
    display_text(350,-3,r_ph,'white' ,'Arial',12,'bold')    
    return              


    
'''draw and fillout a rectangle paramaters: x, y starting position w, h widht and heigh, c color'''
def draw_rectangle(x,y,w,h,c):
    t1.begin_fill()
    go_to(x,y)
    t1.pendown()
    t1.color(c)
    for i in range (2):
        t1.forward(w)
        t1.left(90)
        t1.forward(h)        
        t1.left(90)
    t1.end_fill()
    t1.hideturtle()


''' Show a line on the scren: text, x,y, color font size and atribute '''
def display_text(x,y,text,c,fnt,sze,atrb):
    global t1
    t1.color(c)
    go_to(x,y)
    t1.write(text,False, align='left',font =(fnt,sze,atrb))

def initial_turtle():
    global t1
    global window   
    
    ''' using tkinter turtle    '''
    import turtle
    #import tkinter as tk
    #root = tk.Tk()
    #window =tk.Tk()                               ###########
    #window.title("Reading Sensors...")            #############   
    #tk.title("Monitoring")                        3333333333333
    #canvas = tk.Canvas(master = window, width = 1280, height =35,relief = SUNKEN)
    canvas = tk.Canvas(master = frame8, width = 1280, height =35,relief = SUNKEN)
    #canvas.pack()
    t1 = turtle.RawTurtle(canvas)
    #t1.title('Monitoring Window')
    t1.hideturtle()
    #turtle.Screen.bgcolor('gray')
    t1.speed(0)
    #wn=t1.Screen()
    #wn.bgcolor('gray')
    #wn.title('Reading Sensors')
    canvas.grid(row =0, column =0)
    



'''kill turtle'''
def kill_turtle(): 
    global exit_loop    
    exit_loop = True
    return

    
''' board main '''
def monitor_turtle():
    global r_temp 
    global r_dox 
    global r_ph       
    global PH_low_p 
    global PH_high_p
    global DO_low_p 
    global DO_high_p
    global TMP_low_p
    global TMP_high_p
    global exit_loop
    global window    
    update_buttons('disabled')    
    b =''
    initial_turtle()         
    draw_monitoring_screen() 
    while True:
        if exit_loop == False:
            loop_two(b)
            update_screen_values()
        else:
           label_5_1=Label(frame5, text= '                                                  ',width =50, height =height03)          
           label_5_1.grid(row=0, column=0, padx=10, pady =5)            
           label_5_2=Label(frame5, text= '                  ', width =50, height =height03)     
           label_5_2.grid(row=1, column=0, padx=10, pady =5)
           update_buttons('!disabled')
           #t1.reset()
           initial_turtle()
           t1.hideturtle()
           #t1.bgcolor('gray')
           # window.destroy()
           exit_loop = False
           break
    
    return    
    

def write_titles_to_csv():
    global last_saved_csv
    with open('/media/pi/USB DISK/data_log.csv', mode='w') as data_log:        
        now =datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        data_log_writer = csv.writer(data_log, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)        
        data_log_writer.writerow(['Temperature', 'DO', 'PH','Time'])
        last_saved_csv_h = now.strftime("%H")   
        last_saved_csv_m = now.strftime("%M")   
        last_saved_csv_s = now.strftime("%S")
        last_saved_csv = ((float(last_saved_csv_h)*60*60)  + (float(last_saved_csv_m)+60) +(float(last_saved_csv_s))                          
    return    
 


def write_data_to_csv():
    global write_header
    global write_data
    global last_saved_csv
    global r_temp
    global r_dox
    global r_ph
    now =datetime.now()
    string_time = now.strftime("%d/%m/%Y %H:%M:%S")
    with open('/media/pi/USB DISK/data_log.csv', mode='a') as data_log:
        data_log_writer = csv.writer(data_log, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        data_log_writer.writerow([r_temp,r_dox,r_ph,string_time])
        last_saved_csv_h = now.strftime("%H")   
        last_saved_csv_m = now.strftime("%M")   
        last_saved_csv_s = now.strftime("%S")
        last_saved_csv = (float (last_saved_csv_h) *60*60  + float(last_saved_csv_m)+60 +float(last_saved_csv_s)         
    return


def check_csv():
    every_ten =['00','10','20','30','40','50']
    global write_header
    global write_data
    global last_saved_csv
    
    string_hour_now  =''
    string_minute_now  =''
    string_second_now = ''    
    now =datetime.now()
    
    
    string_hour_now = now.strftime("%H")  
    string_minute_now = now.strftime("%M") 
    string_second_now = now.strftime("%S") 
    
    seconds_now = (float(string_hour_now)*60*60) +(float(string_minute_now)*60) +(float(string_second_now)
                                                                                  
    if write_header == True:
        write_titles_to_csv()
        write_header = False


    if (string_minute_now in every_ten) and (seconds_now - last_saved_csv >= 600)                                                                             
       write_data = True
    if write_data == True:    
       write_data_to_csv( )   
       write_data = False      
    else:
        return







#=================================
# Main Window 
#=================================
  
if __name__ == "__main__":

    #==============
    # Main Window s
    #==============
    root = Tk()
    root.title('Environmental Technologies, Inc.')
    #root.geometry('1000x500+1+1')s
    root.geometry('1280x800+1+1')

    ################
    #from Tkinter import *
    #from Tkinter import ttk
      
    root.resizable(False, False)                               
    # window.configure(background='#e6f9ff')
    panedwindow  = ttk.Panedwindow(root, orient = VERTICAL)
    panedwindow.pack(fill =BOTH, expand = False)
    #==================================                   
    # All frames
    #==================================
    frame1 = ttk.Frame(panedwindow, width =100, height =210, relief = SUNKEN)
    frame2 = ttk.Frame(panedwindow, width =100, height =210, relief = SUNKEN)
    frame3 = ttk.Frame(panedwindow, width =100, height =200, relief = SUNKEN)
    frame4 = ttk.Frame(panedwindow, width =100, height =300, relief = SUNKEN)    
    frame5 = ttk.Frame(panedwindow, width =100, height =100, relief = SUNKEN)
    frame6 = ttk.Frame(panedwindow, width =100, height =300, relief = SUNKEN)
    frame7 = ttk.Frame(panedwindow, width =100, height =10, relief = SUNKEN)
    frame8 = ttk.Frame(panedwindow, width =100, height =100, relief = SUNKEN)


    
    #==================================                   
    # Add all panes
    #==================================
    panedwindow.add(frame1, weight = 1)
    panedwindow.add(frame2, weight = 1)
    panedwindow.add(frame3, weight = 1)
    panedwindow.add(frame4, weight = 1)   
    panedwindow.add(frame5, weight = 1)      
    panedwindow.add(frame6, weight = 1)
    panedwindow.add(frame7, weight = 1)
    panedwindow.add(frame8, weight = 1)
    #==================================================
    #  Pane Window 1  - Frame 1 header and logo
    # =================================================
    # Frame 1
    label_1=Label(frame1, text = '   Environmental Technologies, Inc.' ,width =1270, height =220)         #81010 100 
    logo = PhotoImage(file="/home/pi/st/static/ETI_LOGO.gif")

    #logo = PhotoImage(file=".//Aegir-master/static/ETI_LOGO.gif")
    small_logo =logo.subsample(2,2)
    label_1.config(font=("Times New Roman", 17,'bold'))
    label_1.config(image = small_logo)     
    label_1.config(foreground ='navy blue')
    label_1.config(background ='white')
    label_1.config(compound = 'left')
    label_1.config(anchor = 'w')
    label_1.grid(row=0, column=0, padx =1, pady=1)
    
    #===================================================
    #  Pane Window 2 - Frame 2 update readingd and bars
    # ==================================================
    ''' Frame 2
    #update_readings()
    #update_bars()'''

    #===================================================
    #  Pane Window 3   - Frame 3 High and  low
    # ==================================================
    # Frame 3
    #initial_frame3()

    #===================================================
    #  Pane Window 4   - Frame 4 display update buttons
    # ==================================================
    # Frame 4
    #display_update_buttons()
        
    # =====================================================
    # Pane Window 5 - manual test pumps -  test module only
    #======================================================
    # Frame5   
    

    # ==================================
    # Pane Window 6  pumps initial state
    # ==================================
    # Frame 6 
    #initial_pumps()

    #=============================                   
    # Pane Window 7  Start button
    # ============================   
    #initial_frame7()

    #============================
    # main loop
    # ==========================
    # previous initial_loop()  
    #
    restore_files()    
    update_readings()
    update_bars()
    initial_frame3()    
    #display_update_buttons()
    update_buttons('!disabled')
    initial_pumps()
    initial_frame7()
    write_titles_to_csv()
    write_data_to_csv()       
    
    root.mainloop()
    
 
   

  


