#!/usr/bin/python
# -*- coding: latin-1 -*-

import os
from ConfigParser import SafeConfigParser

class Propiedades:
    # variables de clase
    ficheroIni = "config.ini"
    bApt = False
    bGit = False
    bDocker = False

    def __init__(self):
        self.seccion = "Config"
        self.check_config_file()

    # Verifica si existe el fichero de configuración y si no existe lo crea
    def check_config_file(self):
        directory = os.getenv("HOME")+'/.config/indicador-proxy'
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.config_file = directory + '/' + self.ficheroIni
        if (not os.path.exists(self.config_file)):
            self.config = SafeConfigParser()
            self.config.read(self.config_file)
            self.config.add_section(seccion)
            self.config.set(self.seccion,"proxy_apt", "False")
            self.config.set(self.seccion,"proxy_git", "False")
            self.config.set(self.seccion,"proxy_docker", "False")
            with open(self.config_file, 'wb') as configfile:
                self.config.write(configfile)
          
    def lee(self, clave):
        self.config = SafeConfigParser()
        self.config.read(self.config_file)
        try:
            return self.config.get(self.seccion, clave )
        except:
            pass

    def escribe(self, clave, valor):
        self.config.set(self.seccion, clave, str(valor))
        with open(self.config_file, 'wb') as configfile:
            self.config.write(configfile)

 


 

