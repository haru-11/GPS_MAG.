# -*- coding: utf-8 -*-

import serial
import time
import threading

time.sleep(1.0)
s = serial.Serial('/dev/serial0', 115200, timeout=10)

s.readline()

def get_gps():
	while True:

		sentence = s.readline().decode('utf-8')
		print(sentence)

		#時間
		h = int(sentence[7]+sentence[8]) + 9
		if h > 23:
			h - 24
		time = str(h)+sentence[9]+sentence[10]+sentence[11]+sentence[12]+sentence[13]+sentence[14]+sentence[15]+sentence[16]
		print(time)

		#緯度経度
		lat = float(sentence[20]+sentence[21]) + float(sentence[22]+sentence[23]+sentence[24]+sentence[25]+sentence[26]+sentence[27]+sentence[28])/60
		lon = float(sentence[32]+sentence[33]+sentence[34]) + float(sentence[35]+sentence[36]+sentence[37]+sentence[38]+sentence[39]+sentence[40]+sentence[41])/60
		if sentence[43] == 'W':
			lon = 0.0 - lon
		print(str(lat)+','+str(lon))

		#速度
		speed = float(sentence[45]+sentence[46]+sentence[47]+sentence[48]) * 1.852
		print(str(speed))

		#方位
		if sentence[55] == ',':
			dir = sentence[50]+sentence[51]+sentence[52]+sentence[53]+sentence[54]
		else :
			dir = sentence[50]+sentence[51]+sentence[52]+sentence[53]+sentence[54]+sentence[55]
		print(dir)



gpsthread = threading.Thread(target=get_gps, args=()) # 上の関数を実行するスレッドを生成
gpsthread.daemon = True
gpsthread.start() # スレッドを起動

try:

	while True:
		print("OKOKOKOKOKOKOK!!!!!!!")
		time.sleep(1.0)

except KeyboardInterrupt:
	s.close()
	pass
