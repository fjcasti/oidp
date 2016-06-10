#!/usr/bin/python
# -*- coding: latin-1 -*-
import sys
from gi.repository import Gtk as gtk
from gi.repository import Gio 
from gi.repository import AppIndicator3 as appindicator
import re
import os
from os.path import expanduser
from config_win import ConfigWin
from propiedades import Propiedades
from registro import Registro
import ConfigParser
from shutil import copyfile

class IndicadorProxy:
    configWin = None
    objRegistro = None
    objPropiedades = None

    def __init__(self):
        global proxy_estado

        # fichero de propiedades
        self.objPropiedades = Propiedades()

        # acceso al registro dconf
        self.objRegistro = Registro()

        # leer el estado del proxy
        proxy_estado=self.objRegistro.getStatus()
        print("[INFO]:  Estado del proxy: " + proxy_estado)

        # configuración del icono
        self.ind = appindicator.Indicator.new("indicador-proxy", "estado del proxy", appindicator.IndicatorCategory.APPLICATION_STATUS)
        base_dir=os.path.abspath(os.path.dirname(sys.argv[0]))
        self.ind.set_icon(os.path.join(base_dir,'ind-con-proxy.png'))
        self.ind.set_attention_icon (os.path.join(base_dir,'ind-sin-proxy.png'))
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        if proxy_estado == "none":
            self.ind.set_status(appindicator.IndicatorStatus.ATTENTION)

        # establece el menú de la aplicación
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

        # self.menu_prueba = gtk.MenuItem("Prueba")
        # self.menu_prueba.connect("activate", self.prueba)
        # self.menu.append(self.menu_prueba)
        # self.menu_prueba.show()

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
        print("[DEBUG]: Activar proxy")
       
        # leer información del registro
        servidor = self.objRegistro.getHost()
        puerto   = self.objRegistro.getPort()
        usarusu  = self.objRegistro.getAuthentication()
        usuario  = self.objRegistro.getUser()
        clave    = self.objRegistro.getPassword()

        # activa en el registro el proxy
        self.objRegistro.setStatus('manual')


        # estableciendo proxy para aplicaciones de consola (.bashrc)                
        self.pon_proxy_bashrc(servidor, puerto, usuario, clave)

        if (self.objPropiedades.lee("proxy_apt") == "True"):
            # Establece el proxy para 'apt-conf'
            self.pon_proxy_apt_conf(servidor, puerto, usuario, clave)

        if (self.objPropiedades.lee("proxy_git") == "True"):
            # Establece el proxy para 'git'
            self.pon_proxy_git(servidor, puerto, usuario, clave)

        if (self.objPropiedades.lee("proxy_docker") == "True" ):
            # Establece el proxy para 'docker'
            self.pon_proxy_docker(servidor, puerto, usuario, clave)

        # modificando menu e icono
        self.menu_activar.hide()
        self.menu_desactivar.show()
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)


    def desactiva_proxy(self, widget):
        print ("[DEBUG]: Quitar proxy")
        # Desactivando el proxy en el registro
        self.objRegistro.setStatus('none')

        # Desactivando el proxy para las aplicaciones de consola (.bashrc)
        self.quita_proxy_bashrc()
        self.quita_proxy_apt_conf()
        self.quita_proxy_docker()

        # modificando menu e icono
        self.menu_activar.show()
        self.menu_desactivar.hide()
        self.ind.set_status(appindicator.IndicatorStatus.ATTENTION)

    # Opción al seleccionar 'configurar'
    def configurar(self, widget):
        if self.configWin is None:
            self.configWin = ConfigWin()
        else:
            self.configWin.__init__()
        self.configWin.show()


    # Opción que se lanza al seleccionar el menú prueba
    def prueba(self, widget):
        print ("[DEBUG]  Prueba")
        

    # Activa el proxy en el fichero ~/.bashrc
    def pon_proxy_bashrc(self, proxy, puerto, usuario, clave):
        print "[DEBUG]: establecer proxy en ~/.bashrc"
        home = expanduser("~")
        f = home+"/.bashrc"
        try:
            fichero = open(f, "a")
            if (usuario):
                print "[DEBUG] USAR validacion de usuario"
                fichero.write("export HTTP_PROXY=\"http://%s:%s@%s:%s\"\n" % (usuario, clave, proxy, puerto))
                fichero.write("export HTTPS_PROXY=\"https://%s:%s@%s:%s\"\n" % (usuario, clave, proxy, puerto))
                fichero.write("export FTP_PROXY=\"ftp://%s:%s@%s:%s\"\n" % (usuario, clave, proxy, puerto))
            else:
                print "[DEBUG] SIN validacion de usuario"
                fichero.write("export HTTP_PROXY=\"http://%s:%s\"\n" % (proxy, puerto))
                fichero.write("export HTTPS_PROXY=\"https://%s:%s\"\n" % (proxy, puerto))
                fichero.write("export FTP_PROXY=\"ftp://%s:%s\"\n" % (proxy, puerto))

            fichero.write("export NO_PROXY=\"%s\"\n" % (strExcepciones))
            fichero.close()
        except:
            pass
 
    # Desactivando el proxy para las aplicaciones de consola (.bashrc)    
    def quita_proxy_bashrc(self):
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

    # Escribe los parametros dados en el fichero /etc/apt/apt.conf
    # en caso de usar apt-add-repository es necesario usar root para ello hay que 
    # establecer el proxy para usuario root tambien (/etc/bash/bashrc)
    def pon_proxy_apt_conf(self, proxy, puerto, usuario, clave):   
        print "[DEBUG]: establecer proxy para apt-get"
        comandoSudo = "gksudo -m 'Introduzca su contraseña para realizar cambios en el sistema' -- bash -c '"
        borraFichero1=""
        try:
            fichero1 = "/etc/apt/apt.conf"
            fichero2 = "apt.conf"

            copyfile(fichero1, fichero2)
            f = open(fichero2, "a")
            if (usuario):
                f.write('Acquire::%s::proxy "%s://%s:%s@%s:%s/";\n' % ("ftp","ftp",usuario,clave, proxy, puerto))
                f.write('Acquire::%s::proxy "%s://%s:%s@%s:%s/";\n' % ("http","http",usuario,clave, proxy, puerto))
                f.write('Acquire::%s::proxy "%s://%s:%s@%s:%s/";\n' % ("https","https",usuario,clave, proxy, puerto))
            else:
                f.write('Acquire::%s::proxy "%s://%s:%s/";\n' % ("ftp","ftp", proxy, puerto))
                f.write('Acquire::%s::proxy "%s://%s:%s/";\n' % ("http","http", proxy, puerto))
                f.write('Acquire::%s::proxy "%s://%s:%s/";\n' % ("https","https", proxy, puerto))
            f.close()
            comandoSudo +=  'cp ' + fichero2 + ' ' + fichero1 + '; '
            borraFichero1=fichero2
        except:
            pass             


        try:

            fichero1 = "/etc/bash.bashrc"
            fichero2 = "etc.bashrc"
            copyfile(fichero1, fichero2)
            f = open(fichero2, "a")
            if (usuario):
                f.write("export HTTP_PROXY=\"http://%s:%s@%s:%s\"\n" % (usuario, clave, proxy, puerto))
                f.write("export HTTPS_PROXY=\"https://%s:%s@%s:%s\"\n" % (usuario, clave, proxy, puerto))
                f.write("export FTP_PROXY=\"ftp://%s:%s@%s:%s\"\n" % (usuario, clave, proxy, puerto))
            else:
                f.write("export HTTP_PROXY=\"http://%s:%s\"\n" % (proxy, puerto))
                f.write("export HTTPS_PROXY=\"https://%s:%s\"\n" % (proxy, puerto))
                f.write("export FTP_PROXY=\"ftp://%s:%s\"\n" % (proxy, puerto))
            f.close()
            comandoSudo += 'cp ' + fichero2 + ' ' + fichero1 + "'"
            os.system(comandoSudo)
            os.remove(borraFichero1)
            os.remove(fichero2)
        except:
            pass             

    def quita_proxy_apt_conf(self):         
        print "[DEBUG]: eliminar proxy para apt-get"
        nombre="apt.conf"
        comandoSudo = "gksudo -m 'Introduzca su contraseña para realizar cambios en el sistema' -- bash -c '"
        borraFichero1=""
        try:
            fichero1 = "/etc/apt/apt.conf"
            fichero2 = "apt.conf"

            copyfile(fichero1, fichero2)
            f = open(nombre, "r")
            l = f.read()
            l2 = re.sub(r'\n?(.*Acquire::.*::proxy\s*".*"\;)', "", l)
            f.close()
            if (not l2 == l):
                f = open(fichero2, 'w')
                f.write(l2)
                f.close()            

                comandoSudo += ' cp ' + fichero2 + '  ' + fichero1 + "; "
                borraFichero1=fichero2

            
            fichero1 = "/etc/bash.bashrc"
            fichero2 = "etc.bashrc"
            copyfile(fichero1, fichero2 )
            f = open(fichero2, 'r')
            l = f.read()
            l = re.sub(r'\n?(.*HTTP_PROXY\s*=\s*".*")', "", l)
            l = re.sub(r'\n?(.*HTTPS_PROXY\s*=\s*".*")', "", l)
            l = re.sub(r'\n?(.*FTP_PROXY\s*=\s*".*")', "", l)
            l = re.sub(r'\n?(.*NO_PROXY\s*=\s*".*")', "", l)
            f.close()

            f = open(fichero2, 'w')
            f.write(l)
            f.close()
            comandoSudo += ' cp ' + fichero2 + '  ' + fichero1 + "' "
            os.system(comandoSudo)


            os.remove(borraFichero1)
            os.remove(fichero2)
            

        except:
            pass             

    # Escribe los parametros dados en el fichero ~/.gitconfig
    def pon_proxy_git(self, proxy, puerto, usuario, clave):   
        home = expanduser("~") 
        fich = home+"/.gitconfig"
        config = ConfigParser.RawConfigParser()
        config.read(fich)
        valor="http://"+ usuario + ":" + clave + "@" + proxy + ":" + puerto
        print "[DEBUG]: ", valor
        config.set('http', 'proxy', valor)
        with open(fich, 'wb') as configfile:
            config.write(configfile)

    def quita_proxy_git(self):
        home = expanduser("~")
        fich = home+"/.gitconfig"
        config = ConfigParser.RawConfigParser()
        config.read(fich)

        config.remove_option("http", "proxy")
        with open(fich, 'wb') as configfile:
            config.write(configfile)

   # Activa el proxy para docker /etc/default/docker
    def pon_proxy_docker(self, proxy, puerto, usuario, clave):
        print "[DEBUG]: establecer proxy en /etc/default/docker"
        
        fich = "/etc/default/docker"
        try:
            fichero = open(fich, "a")
            if (usuario):
                print "[DEBUG]: pon_proxy_docker: con validacion de usuario"
                fichero.write("export HTTP_PROXY=\"http://%s:%s@%s:%s\"\n" % (usuario, clave, proxy, puerto))
                fichero.write("export HTTPS_PROXY=\"https://%s:%s@%s:%s\"\n" % (usuario, clave, proxy, puerto))
            else:
                print "[DEBUG]: pon_proxy_docker"
                fichero.write("export HTTP_PROXY=\"http://%s:%s\"\n" % (proxy, puerto))
                fichero.write("export HTTPS_PROXY=\"https://%s:%s\"\n" % (proxy, puerto))

            fichero.write("export NO_PROXY=\"%s\"\n" % (strExcepciones))
            fichero.close()
        except:
            pass

    # Desactivando el proxy para las aplicaciones de consola (.bashrc)    
    def quita_proxy_docker(self):
        fich = "/etc/default/docker"

        try:
            f = open(fich, 'r')
            l = f.read()
            l = re.sub(r'\n?(.*_PROXY\s*=\s*".*")', "", l)
            f.close()
            f = open(fichero, 'w')
            f.write(l)
            f.close()
        except:
            pass




if __name__ == "__main__":
    indicator = IndicadorProxy()
    gtk.main()

