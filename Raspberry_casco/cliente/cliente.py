from wifi import Cell, Scheme
from uuid import getnode
import threading
import time
import socket
import sys
import json
import pygame
from grafico import interfaz
import signal
import ConfigParser
import os

base_path = None
puerto = None
ip = None
nombre = None
entorno = None
umbral_calidad  = None
frecuencia_escaneo = None
frecuencia_heartbeat = None
tiempo_mostrar_notas = None
tiempo_mostrar_medidas = None
tiempo_mostrar_error = None

def configurar():
	global base_path, ip, puerto, nombre,frecuencia_escaneo,tiempo_mostrar_notas
	global tiempo_mostrar_medidas, tiempo_mostrar_error, frecuencia_heartbeat, umbral_calidad 
	config = ConfigParser.ConfigParser()
	base_path = os.getcwd() + '/'
	try:
		config.read("config.conf")
		nombre = config.get('GENERAL', 'nombre')
		ip = config.get('CONEXION',"ip")
		puerto = int(config.get('CONEXION', 'puerto'))
		frecuencia_escaneo = int(config.get('SISTEMA', 'frecuencia_escaneo'))
		tiempo_mostrar_notas = int(config.get('SISTEMA', 'tiempo_mostrar_notas'))
		frecuencia_heartbeat = int(config.get('SISTEMA', 'frecuencia_heartbeat'))
		tiempo_mostrar_medidas = int(config.get('SISTEMA', 'tiempo_mostrar_medidas'))
		tiempo_mostrar_error = int(config.get('SISTEMA', 'tiempo_mostrar_error'))
		umbral_calidad  = int(config.get('SISTEMA', 'umbral_calidad'))
	except Exception as e:
		print("Excepcion al configurar")
		print(e)
		sys.exit(-1)

def handle_sigint(signal, frame):
	global entorno
	entorno.cerrar_entorno()
	print("Capturado ctrl+c")
	sys.exit(0)

def reproducir_audio(path):
	global base_path
	path = base_path + path
	pygame.mixer.init()
	pygame.mixer.music.load(path)
	pygame.mixer.music.play()
	while pygame.mixer.music.get_busy() == True:
		continue
	

def get_mac():
	mac = str(hex(getnode())) #0xaabbccddeeffL
	mac = mac[2:len(mac)-1].upper() #AABBCCDDEEFF
	return ':'.join(mac[i:i+2] for i in range(0,12,2)) #AA:BB:CC:DD:EE:FF
	
def escanear_redes():
	try:
		redes = Cell.all("wlan0")
	except Exception as e:
		return None
	mejor_calidad=umbral_calidad #umbral de calidad, el maximo es 70
	calidad = None
	mac = None
	for red in redes:		
		if red.ssid.startswith("VM-"):
			calidad = int(red.quality[0:2])
			if (calidad >= mejor_calidad):
				mejor_calidad = calidad #red.signal en DBM
				mac = red.ssid[3:len(red.ssid)] #red.address -> comportamientos inesperados, devuelve MAC con un byte erroneo
	return mac
	
def conectar():
	t_reconectar = 5
	global entorno, ip, puerto, nombre, frecuencia_escaneo, tiempo_mostrar_notas
	global tiempo_mostrar_medidas, tiempo_mostrar_error, frecuencia_heartbeat
	while True:
		try: 
			entorno.escribir(0,0,"Conectando...")
			conexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			direccion = (ip, puerto)
			conexion.connect(direccion)
			alta = "POST /newnode HTTP/1.1\n\n"
			alta+= '{ "NOMBRE" : "' + nombre + '", "TIPO" : "CASCO", "MAC" : "' + get_mac() + '" }' 
			conexion.send(alta.encode())
			recibido=conexion.recv(1024)
			reproducir_audio("sonidos/conectado.wav")
			entorno.escribir(0,0,"Conectado")
			vueltas = 0
			while(True):
				try:
					mac = escanear_redes()
					if mac != None:
						vueltas=0
						peticion = "GET /resource HTTP/1.1\n\n"
						peticion+= '{ "MAC" : "' + mac + '" }'
						conexion.send(peticion)
						bytes_datos = conexion.recv(2048)
						recibido=bytes_datos.decode("utf-8")
						paquete=recibido.split("\n\n")
						if "OK" in paquete[0]: #paquete[0] -> cabecera del paquete
							reproducir_audio("sonidos/info_disponible.wav")
							info = json.loads(paquete[1])
							if info["TIPO"] == "NOTA":
								if info["NOTA"] == "":
									entorno.escribir(2,0,"Aun no hay nada asociado",tiempo_mostrar_error) 
								entorno.escribir(2,0,info["NOTA"], tiempo_mostrar_notas)
							elif info["TIPO"] == "MEDIDAS":
								mostrar=""
								for medida in info["MEDIDAS"]:
									mostrar+= medida["PARAMETRO"] + ": " + str(medida["VALOR"]) + medida["UNIDAD"] +"\n"
								if mostrar != "":
									entorno.escribir(2,0,mostrar,tiempo_mostrar_medidas)
								else: entorno.escribir(2,0,"Aun no hay medidas registradas",tiempo_mostrar_error)
							else:
								reproducir_audio("sonidos/error.wav") 
								entorno.escribir(2,0,"Tipo de informacion no soportada",tiempo_mostrar_error)  		
						else: 
							reproducir_audio("sonidos/error.wav") 
							entorno.escribir(2,0,"Ha ocurrido un error",tiempo_mostrar_error)   	
					else:
						vueltas+= 1
						time.sleep(frecuencia_escaneo)
					if vueltas == frecuencia_heartbeat:
						vueltas = 0 
						peticion = "POST /heartbeat HTTP/1.1\n\n"
						conexion.send(peticion)
						recibido=conexion.recv(1024)
				except Exception as e:
					t_reconectar = 5
					entorno.escribir(0,0,"Desconectado")
					reproducir_audio("sonidos/desconectado.wav")
					break
			time.sleep(t_reconectar)
			if (t_reconectar < 160):
				t_reconectar*= 2
		except Exception as e:
			pass

def main():
	signal.signal(signal.SIGINT, handle_sigint)
	configurar()
	global entorno
	entorno = interfaz()
	entorno.iniciar_entorno()
	conectar()
	
main()
