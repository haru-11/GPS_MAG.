# -*- coding: utf-8 -*-

import serial
import micropyGPS
import threading
import math
import time

pi = 3.1415926535
goal_latitude = 35.623575	#ゴールの緯度（10進法，南緯は負の数）
goal_longitude = 139.391182	#ゴールの経度（10進法，西経は負の数）
radius = 6378.137	#地球の半径km

gps = micropyGPS.MicropyGPS(9, 'dd') # MicroGPSオブジェクトを生成する。
                                     # 引数はタイムゾーンの時差と出力フォーマット

def cal_gps(radius, goal_latitude, goal_longitude, now_lat, now_lon):
	#度をラジアンに変換
	delta_lon = math.radians(goal_longitude - now_lon)
	now_lat = math.radians(now_lat)
	now_lon = math.radians(now_lon)
	goal_latitude = math.radians(goal_latitude)
	goal_longitude = math.radians(goal_longitude)

	#距離方位角計算 https://keisan.casio.jp/exec/system/1257670779
	dist = radius * math.acos(math.sin(goal_latitude)*math.sin(now_lat) + math.cos(goal_latitude)*math.cos(now_lat)*math.cos(delta_lon))
	azi = (180/pi)*math.atan2(math.sin(delta_lon), math.cos(now_lat)*math.tan(goal_latitude) - math.sin(now_lat)*math.cos(delta_lon))
	if azi < 0:
		azi = azi + 360
	return dist, azi

def rungps(): # GPSモジュールを読み、GPSオブジェクトを更新する
    s = serial.Serial('/dev/serial0', 9600, timeout=10)
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

while True:
	if gps.clean_sentences > 20: # ちゃんとしたデーターがある程度たまったら出力する
		h = gps.timestamp[0] if gps.timestamp[0] < 24 else gps.timestamp[0] - 24
		cal = cal_gps(radius, goal_latitude, goal_longitude, gps.latitude[0], gps.longitude[0])
		print('%2d:%02d:%04.1f' % (h, gps.timestamp[1], gps.timestamp[2]))
		print('緯度経度: %2.8f, %2.8f' % (gps.latitude[0], gps.longitude[0]))
		print('海抜: %f' % gps.altitude)
		print('速度: %f [km/h]' % gps.speed[1])
		print('方位: %f' % gps.course)
		print('距離: %f' % cal[0])
		print('方位角: %f' % cal[1])
	time.sleep(1.0)
