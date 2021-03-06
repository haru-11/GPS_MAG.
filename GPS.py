# -*- coding: utf-8 -*-

import serial
import micropyGPS
import threading
import math
import time
import pigpio
pin_sb = 17
gpio_pin0 = 13
in1 = 27
in2 = 22

pi = 3.1415926535
goal_latitude = 35.623575	#ゴールの緯度（10進法，南緯は負の数）
goal_longitude = 139.391182	#ゴールの経度（10進法，西経は負の数）
radius = 6378.137	#地球の半径km

gps = micropyGPS.MicropyGPS(9, 'dd') # MicroGPSオブジェクトを生成する。
                                     # 引数はタイムゾーンの時差と出力フォーマット

pi = pigpio.pi()
pi.set_mode(gpio_pin0, pigpio.OUTPUT)
pi.set_mode(pin_sb, pigpio.OUTPUT)
pi.set_mode(in1, pigpio.OUTPUT)
pi.set_mode(in2, pigpio.OUTPUT)

pi.set_PWM_frequency(pin_sb, 800)
pi.set_PWM_range(pin_sb, 255)
pi.set_PWM_dutycycle(pin_sb, 0)

pi.hardware_PWM(gpio_pin0, 50,( 0.15/20.0) * 1000000)

pi.write(in1, 0)
pi.write(in2, 0)

s = serial.Serial('/dev/serial0', 9600, timeout=10)

def cal_gps(radius, goal_latitude, goal_longitude, now_lat, now_lon):
	#度をラジアンに変換
	delta_lon = math.radians(goal_longitude - now_lon)
	now_lat = math.radians(now_lat)
	now_lon = math.radians(now_lon)
	goal_latitude = math.radians(goal_latitude)
	goal_longitude = math.radians(goal_longitude)

	#距離方位角計算 https://keisan.casio.jp/exec/system/1257670779
	dist = radius * math.acos(math.sin(goal_latitude)*math.sin(now_lat) + math.cos(goal_latitude)*math.cos(now_lat)*math.cos(delta_lon))
	azi = (180.0/3.1415926535)*math.atan2(math.sin(delta_lon), math.cos(now_lat)*math.tan(goal_latitude) - math.sin(now_lat)*math.cos(delta_lon))
	if azi < 0:
		azi = azi + 360.0
	return dist, azi

def rungps(): # GPSモジュールを読み、GPSオブジェクトを更新する

    s.readline() # 最初の1行は中途半端なデーターが読めることがあるので、捨てる
    while True:
        sentence = s.readline().decode('utf-8') # GPSデーターを読み、文字列に変換する
        if sentence[0] != '$': # 先頭が'$'でなければ捨てる
            continue
        for x in sentence: # 読んだ文字列を解析してGPSオブジェクトにデーターを追加、更新する
            gps.update(x)

gpsthread = threading.Thread(target=rungps, args=()) # 上の関数を実行するスレッドを生成
gpsthread.daemon = True
gpsthread.start() # スレッドを起動

def get_gps():

	if gps.clean_sentences > 20: # ちゃんとしたデーターがある程度たまったら出力する
		h = gps.timestamp[0] if gps.timestamp[0] < 24 else gps.timestamp[0] - 24
		cal = cal_gps(radius, goal_latitude, goal_longitude, gps.latitude[0], gps.longitude[0])
		#print('%2d:%02d:%04.1f' % (h, gps.timestamp[1], gps.timestamp[2]))
		#print('緯度経度: %2.8f, %2.8f' % (gps.latitude[0], gps.longitude[0]))
		#print('海抜: %f' % gps.altitude)
		#print('速度: %f [km/h]' % gps.speed[1])
		#print('方位: %f' % gps.course)
		#print('距離: %f' % cal[0])
		#print('方位角: %f' % cal[1])
		return gps.course, gps.speed[1], cal[0], cal[1]
	else:
		return 0, 0, 0, 0
pi.write(in1, 1)
pi.write(in2, 0)
pi.set_PWM_dutycycle(pin_sb, 255)

while True:
	num = get_gps()

	if num[0] > 2:
		if num[1]-num[3] < 10:
			pi.hardware_PWM(gpio_pin0, 50,( 1.0/20.0) * 1000000)
		elif num[1]-num[3] < -10:
			pi.hardware_PWM(gpio_pin0, 50,( 2.0/20.0) * 1000000)
		else:
			pi.hardware_PWM(gpio_pin0, 50,( 1.5/20.0) * 1000000)

		if num[2] < 0.01:
			pi.write(in1, 0)
			pi.write(in2, 0)
			pi.set_PWM_dutycycle(pin_sb, 0)
			s.write("GOAL!!!")
	print("To goal:"+str(num[2])+"[m]")
	print("To goal:"+str(num[3])+"[deg]")
	print("now:"+str(num[1])+"[m/s]")
	print("now:"+str(num[0])+"[deg]")
	s.write("To goal:"+str(num[2])+"[m]")
	s.write("To goal:"+str(num[3])+"[deg]")
	time.sleep(1)
