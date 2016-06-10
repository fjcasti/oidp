#!/usr/bin/python
# -*- coding: latin-1 -*-

import os
from gi.repository import Gio 
from gi.repository import GLib 

class Registro:
    # variables de clase
    gsettings = None
    gsettings_http= None

    def __init__(self):
        self.gsettings = Gio.Settings.new('org.gnome.system.proxy')
        self.gsettings_http= Gio.Settings.new('org.gnome.system.proxy.http')


    def getStatus(self):
        return self.gsettings.get_string('mode')

    # Modos disponibles 'auto', 'none', 'manual'
    def setStatus(self,mode):
        self.gsettings.set_string ('mode', mode)


    # devuelve una cadena con la lista de excepciones separadas por comas.
    def getIgnoreList(self):
        lista_excepciones=self.gsettings.get_value('ignore-hosts')
        strExcepciones=""
        for e in lista_excepciones:
            strExcepciones += e + ", "
        strExcepciones=strExcepciones[:-2]
        return strExcepciones

    # establece la lista de excepciones para el proxy.
    # recibe una cadena con las excepciones separadas por comas.
    def setIgnoreList(self, strExcepciones):
        lista=strExcepciones.split(",")
        self.gsettings.set_value('ignore-hosts', GLib.Variant('as',lista))

    # devuelve la cadena con el nombre del servidor proxy
    def getHost(self):
        return self.gsettings_http.get_string('host')

    # establece el nombre/IP del servidor proxy
    def setHost(self, host):
        self.gsettings_http.set_string('host', host)


    def getPort(self):
        return str(self.gsettings_http.get_int('port'))

    # establece el puerto de conexión al proxy
    # recibe el valor como una cadena
    def setPort(self, port):
        self.gsettings_http.set_int('port', int(port))


    # devuelve la cadena True/False indicando si hay que autentificar o no.
    def getAuthentication(self):
        return str(self.gsettings_http.get_boolean('use-authentication'))


    # establece si hay que validar o no al usuario en el proxy configurado
    # recibe un valor booleano
    def setAuthentication(self, auth):
        self.gsettings_http.set_boolean('use-authentication', auth)



    def getUser(self):
        return self.gsettings_http.get_string('authentication-user')

    # recibe una cadena con el nombre del usuario.
    def setUser(self, user):
        self.gsettings_http.set_string('authentication-user', user)

    def getPassword(self):
        return self.gsettings_http.get_string('authentication-password')

    def setPassword(self, password):
        self.gsettings_http.set_string('authentication-password', password)