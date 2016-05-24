#!/usr/bin/python
# -*- coding: latin-1 -*-
import sys
from gi.repository import Gtk as gtk
from gi.repository import Gio 
from gi.repository import AppIndicator3 as appindicator
import subprocess
import re
import os
from os.path import expanduser
from config_win import ConfigWin
import ConfigParser
from shutil import copyfile

class IndicadorProxy:
    configWin = None
    gsettings = None
    gsettings_http = None
    def __init__(self):
        global proxy_estado
        global gsettings
        global gsettings_http

        # leer el estado del proxy
        gsettings = Gio.Settings.new('org.gnome.system.proxy')
        gsettings_http= Gio.Settings.new('org.gnome.system.proxy.http')
        proxy_estado=gsettings.get_string('mode')
        print("[INFO]:  Estado del proxy: " + proxy_estado)

        self.ind = appindicator.Indicator.new("indicador-proxy", "estado del proxy", appindicator.IndicatorCategory.APPLICATION_STATUS)
        base_dir=os.path.abspath(os.path.dirname(sys.argv[0]))
        # print ("[DEBUG]: directorio base:" + base_dir)
        self.ind.set_icon(os.path.join(base_dir,'ind-con-proxy.png'))
        self.ind.set_attention_icon (os.path.join(base_dir,'ind-sin-proxy.png'))
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        if proxy_estado == "none":
            self.ind.set_status(appindicator.IndicatorStatus.ATTENTION)

        # leer fichero configuración 
        self.check_config_file()

        self.menu_setup()
        self.ind.set_menu(self.menu)

    def menu_setup(self):
        global proxy_estado
        self.menu = gtk.Menu()

        self.menu_activar = gtk.MenuItem("Usar proxy")
        self.menu_activar.connect("activate", self.activa_proxy)
        self.menu.append(self.menu_activar)
        self.menu_desactivar = gtk.MenuItem("Sin proxy")
        self.menu_desactivar.connect("activate", self.desactiva_proxy)
        self.menu.append(self.menu_desactivar)

        if proxy_estado == "none":	
            self.menu_activar.show()
        else:
            self.menu_desactivar.show()

        self.blanco_item = gtk.MenuItem()
        self.blanco_item.show()
        self.menu.append(self.blanco_item)

        self.menu_configurar = gtk.MenuItem("Configurar")
        self.menu_configurar.connect("activate", self.configurar)

        self.menu.append(self.menu_configurar)
        self.menu_configurar.show()

        self.menu_prueba = gtk.MenuItem("Prueba")
        self.menu_prueba.connect("activate", self.prueba)
        self.menu.append(self.menu_prueba)
        self.menu_prueba.show()

        self.blanco_item = gtk.MenuItem()
        self.blanco_item.show()
        self.menu.append(self.blanco_item)

        self.quit_item = gtk.MenuItem("Quit")
        self.quit_item.connect("activate", self.quit)
        self.quit_item.show()
        self.menu.append(self.quit_item)

    def quit(self, widget):
        sys.exit(0)

    def  activa_proxy(self, widget):
        global gsettings_http
        global gsettings
        print("[DEBUG]: Activar proxy")

        # objetos para acceder al registro
        # gsettings = Gio.Settings.new('org.gnome.system.proxy')
        # gsettings_http = Gio.Settings.new('org.gnome.system.proxy.http')
        
        # leer información del registro
        servidor=gsettings_http.get_string('host')
        puerto  =str(gsettings_http.get_int('port'))
        usarusu =gsettings_http.get_boolean('use-authentication')
        usuario =gsettings_http.get_string('authentication-user')
        clave   =gsettings_http.get_string('authentication-password')

        # leer la información de configuracion
        self.config_file = os.getenv("HOME")+'/.config/indicador-proxy/config.ini'
        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.config_file)

        # activa en registro el proxy
        gsettings.set_string('mode', 'manual')

        # leyendo la lista de excepciones y creando una cadena con ella
        lista_excepciones=gsettings.get_value('ignore-hosts')
        strExcepciones=""
        for e in lista_excepciones:
            strExcepciones += e + ", "
        strExcepciones=strExcepciones[:-2]


        # estableciendo proxy para aplicaciones de consola (.bashrc)                
        home = expanduser("~")
        f = home+"/.bashrc"
        print "[DEBUG]: ~/.bashrc ", f
        try:
            fichero = open(f, "a")
            if (usarusu):
                print "[DEBUG] USAR validacion de usuario"
                fichero.write("export HTTP_PROXY=\"http://%s:%s@%s:%s\"\n" % (usuario, clave, servidor, puerto))
                fichero.write("export HTTPS_PROXY=\"https://%s:%s@%s:%s\"\n" % (usuario, clave, servidor, puerto))
                fichero.write("export FTP_PROXY=\"ftp://%s:%s@%s:%s\"\n" % (usuario, clave, servidor, puerto))
            else:
                print "[DEBUG] SIN validacion de usuario"
                fichero.write("export HTTP_PROXY=\"http://%s:%s\"\n" % (servidor, puerto))
                fichero.write("export HTTPS_PROXY=\"https://%s:%s\"\n" % (servidor, puerto))
                fichero.write("export FTP_PROXY=\"ftp://%s:%s\"\n" % (servidor, puerto))

            fichero.write("export NO_PROXY=\"%s\"\n" % (strExcepciones))
            fichero.close()
        except:
            pass

        # Establece el proxy para 'apt-conf'
        self.pon_proxy_apt_conf(servidor, puerto, usuario, clave)

        self.menu_activar.hide()
        self.menu_desactivar.show()
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)


    def desactiva_proxy(self, widget):
        print ("[DEBUG]: quitando proxy")
        # Desactivando el proxy en el registro
        gsettings = Gio.Settings.new('org.gnome.system.proxy')
        gsettings.set_string('mode', 'none')
        # gsettings = Gio.Settings.new('org.gnome.system.proxy.http')
        # gsettings.set_string('authentication-password', '')
        # gsettings.set_string('authentication-user',  '')
        # gsettings.set_boolean('enabled',  'false')
        # gsettings.set_string('host', '')
        # gsettings.set_int('port', 8080)
        # gsettings.set_boolean('use-authentication', 'false')

        # Desactivando el proxy para las aplicaciones de consola (.bashrc)
        home = expanduser("~")
        fichero = home + "/.bashrc"
        print "[DEBUG]: quitando en ~/.bashrc ", fichero
        try:
            f = open(fichero, 'r')
            l = f.read()
            l = re.sub(r'\n?(.*HTTP_PROXY\s*=\s*".*")', "", l)
            l = re.sub(r'\n?(.*HTTPS_PROXY\s*=\s*".*")', "", l)
            l = re.sub(r'\n?(.*FTP_PROXY\s*=\s*".*")', "", l)
            l = re.sub(r'\n?(.*NO_PROXY\s*=\s*".*")', "", l)
            f.close()
            f = open(fichero, 'w')
            f.write(l)
            f.close()
        except:
            pass

        self.quita_proxy_apt_conf()


        self.menu_activar.show()
        self.menu_desactivar.hide()
        self.ind.set_status(appindicator.IndicatorStatus.ATTENTION)

    # Verifica si existe el fichero de configuración y si no existe lo crea
    def check_config_file(self):
        directory = os.getenv("HOME")+'/.config/indicador-proxy'
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.config_file = directory + '/config.ini'
        if (not os.path.exists(self.config_file)):
            lines = []
            lines.append('[Configuracion]\n')
            lines.append('proxy_apt = False\n')
            try:
                file =  open(self.config_file, "w+")
                for line in lines:
                    file.write(line)
                file.close()
            except:
                pass

    # lee datos del fichero INI de momento siempre la misma clave 'proxy_apt'
    def lee_conf_apt(self):
        retorno = False
        self.config_file = os.getenv("HOME")+'/.config/indicador-proxy/config.ini'
        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.config_file)
        if self.config.get('Configuracion', 'proxy_apt') == 'True':
            retorno = True
        return retorno

    # Opción al seleccionar 'configurar'
    def configurar(self, widget):
        # subprocess.call("")
        #ficherinGlade = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'indicador-proxy.glade')
        if self.configWin is None:
            self.configWin = ConfigWin()
        else:
            self.configWin.__init__()
        self.configWin.show()


    # Opción que se lanza al seleccionar el menú prueba
    def prueba(self, widget):
        print ("[DEBUG]  Prueba")

    # Escribe los parametros dados en el fichero /etc/apt/apt.conf
    def pon_proxy_apt_conf(self, proxy, puerto, usuario, clave):   
        print "[DEBUG]: params"      , proxy, puerto, usuario, clave
        if (self.lee_conf_apt()):
            print "[DEBUG]: establecer proxy para apt-get"
            copyfile("/etc/apt/apt.conf", "apt.conf")
            try:
                fichero = open("apt.conf", "a")
                if (usuario):
                    print "[DEBUG]: USAR validacion de usuario"
                    fichero.write('Acquire::%s::proxy "%s://%s:%s@%s:%s/";\n' % ("ftp","ftp",usuario,clave, proxy, puerto))
                    fichero.write('Acquire::%s::proxy "%s://%s:%s@%s:%s/";\n' % ("http","http",usuario,clave, proxy, puerto))
                    fichero.write('Acquire::%s::proxy "%s://%s:%s@%s:%s/";\n' % ("https","https",usuario,clave, proxy, puerto))
                else:
                    print "[DEBUG]: SIN validacion de usuario"
                    fichero.write('Acquire::%s::proxy "%s://%s:%s/";\n' % ("ftp","ftp", proxy, puerto))
                    fichero.write('Acquire::%s::proxy "%s://%s:%s/";\n' % ("http","http", proxy, puerto))
                    fichero.write('Acquire::%s::proxy "%s://%s:%s/";\n' % ("https","https", proxy, puerto))
                fichero.close()
                print "[DEBUG]: gksudo"
                comandoSudo = 'gksudo cp apt.conf /etc/apt/apt.conf'
                os.system(comandoSudo)
                os.remove("apt.conf")
            except:
                pass             

    # Escribe los parametros dados en el fichero /etc/apt/apt.conf
    def quita_proxy_apt_conf(self):         
        print "[DEBUG]: eliminar proxy para apt-get"
        copyfile("/etc/apt/apt.conf", "apt.conf")
        nombre="apt.conf"
        try:
            fichero = open(nombre, "r")
            l = fichero.read()
            l2 = re.sub(r'\n?(.*Acquire::.*::proxy\s*".*"\;)', "", l)
            fichero.close()
            if (not l2 == l):
                f = open(nombre, 'w')
                f.write(l2)
                f.close()            

                comandoSudo = 'gksudo cp apt.conf /etc/apt/apt.conf'
                os.system(comandoSudo)
                os.remove("apt.conf")
            
        except:
            pass             

# def pon_proxy_bashrc(servidor="proxy.indra.es", puerto="8080", noproxy=""):
#     home = expanduser("~")
#     fRC = home+"/.bashrc"
#     print "[DEBUG]: BRC ", fRC
#     fichero = open(fRC, "a")
#     fichero.write("export http_proxy=\"http://%s:%s\"\n" % (servidor, puerto))
#     fichero.write("export https_proxy=\"https://%s:%s\"\n" % (servidor, puerto))
#     fichero.write("export ftp_proxy=\"ftp://%s:%s\"\n" % (servidor, puerto))
#     fichero.close()

# def quita_proxy_bashrc():
#     home = expanduser("~")
#     fichero = home + "/.bashrc"
#     print "[DEBUG]: quitando en bashrc ", fichero
#     try:
#         f = open(fichero, 'r')
#         l = f.read()
#         l = re.sub(r'\n?(.*http_proxy\s*=\s*".*")', "", l)
#         l = re.sub(r'\n?(.*https_proxy\s*=\s*".*")', "", l)
#         l = re.sub(r'\n?(.*ftp_proxy\s*=\s*".*")', "", l)
#         print l
#         f.close()
#         f = open(fichero, 'w')
#         f.write(l)
#         f.close()
#     except:
#         pass



 
if __name__ == "__main__":
    indicator = IndicadorProxy()
    gtk.main()

