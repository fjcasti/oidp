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
    strCmd = ""
    ficheros = []
    usarSudo = False
      
    def __init__(self):
        # fichero de propiedades
        self.objPropiedades = Propiedades()

        # acceso al registro dconf
        self.objRegistro = Registro()

        # leer el estado del proxy
        estado_proxy=self.objRegistro.getStatus()
        print("[INFO]:  Estado del proxy: " + estado_proxy)

        #limpiando ficheros (aunque puede que aquí no sea suficiente)
        os.system("bash -c 'rm *.temp 2>/dev/null 1> /dev/null '")

        # configuración del icono
        self.ind = appindicator.Indicator.new("indicador-proxy", "estado del proxy", appindicator.IndicatorCategory.APPLICATION_STATUS)
        base_dir=os.path.abspath(os.path.dirname(sys.argv[0]))
        print "[INFO]:  directorio: ", base_dir

        self.ind.set_icon(os.path.join(base_dir,'ind-con-proxy.png'))
        self.ind.set_attention_icon (os.path.join(base_dir,'ind-sin-proxy.png'))
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        if estado_proxy == "none":
            self.ind.set_status(appindicator.IndicatorStatus.ATTENTION)

        # establece el menú de la aplicación
        self.menu_setup(estado_proxy)
        self.ind.set_menu(self.menu)

    def menu_setup(self, estado_proxy):
        self.menu = gtk.Menu()

        self.menu_activar = gtk.MenuItem("Usar proxy")
        self.menu_activar.connect("activate", self.activa_proxy)
        self.menu.append(self.menu_activar)
        self.menu_desactivar = gtk.MenuItem("Sin proxy")
        self.menu_desactivar.connect("activate", self.desactiva_proxy)
        self.menu.append(self.menu_desactivar)

        if estado_proxy == "none":	
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

        self.ficheros = []
        self.usarSudo = False  #de momento false durante la ejecución ya se verá
        # leer información del registro
        servidor = self.objRegistro.getHost()
        puerto   = self.objRegistro.getPort()
        usuario  = None
        clave    = None
        if self.objRegistro.getAuthentication() == "True":
            usuario  = self.objRegistro.getUser()
            clave    = self.objRegistro.getPassword()
        noproxy  = self.objRegistro.getIgnoreList()



        # estableciendo proxy para aplicaciones de consola (.bashrc)                
        self.pon_proxy_bashrc(servidor, puerto, usuario, clave, noproxy)

        
        if (self.objPropiedades.lee("proxy_apt") == "True"):
            # Establece el proxy para 'apt-conf'
            self.pon_proxy_apt_conf(servidor, puerto, usuario, clave, noproxy)

        if (self.objPropiedades.lee("proxy_git") == "True"):
            # Establece el proxy para 'git'
            self.pon_proxy_git(servidor, puerto, usuario, clave)

        if (self.objPropiedades.lee("proxy_docker") == "True" ):
            # Establece el proxy para 'docker'
            self.pon_proxy_docker(servidor, puerto, usuario, clave, noproxy)

        # escribe las modificaciones en los ficheros si todo está OK
        if (self.modifica_ficheros()):
            # activa en el registro el proxy
            self.objRegistro.setStatus('manual')
            # modificando menu e icono
            self.menu_activar.hide()
            self.menu_desactivar.show()
            self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
       
    def desactiva_proxy(self, widget):
        self.ficheros = []
        self.usarSudo = False  #de momento false durante la ejecución ya se verá

        # Desactivando el proxy para las aplicaciones de consola (.bashrc)
        self.quita_proxy_bashrc()      
        self.quita_proxy_apt_conf()    
        self.quita_proxy_git()         
        self.quita_proxy_docker()      

        # escribe las modificaciones en los ficheros si todo está OK
        if (self.modifica_ficheros()):
            # Desactivando el proxy en el registro
            self.objRegistro.setStatus('none')
            # modificando menu e icono
            self.menu_activar.show()
            self.menu_desactivar.hide()
            self.ind.set_status(appindicator.IndicatorStatus.ATTENTION)

    #solicita clave para copiar ficheros del sitema
    # devuelve true si todo está ok sino devuelve False
    def modifica_ficheros(self):
        var=0

        comando= "bash -c '"
        if len(self.ficheros)>0:
            if self.usarSudo:
                comando =  "gksudo -m 'Se requiere su contraseña para realizar los cambios en el sistema' -- bash -c '"

            s = len(self.ficheros)
            for c in xrange(0,s,2):
                comando += "cp " + self.ficheros[c+1] + ' ' + self.ficheros[c] + "; "
            comando += "'"

            var = os.system(comando)
            s = len(self.ficheros)
            for c in xrange(0,s,2):
                os.remove(self.ficheros[c+1])

        retorno= True
        if (var != 0):
            retorno=False

        return retorno

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
    def pon_proxy_bashrc(self, proxy, puerto, usuario, clave, noproxy):
        home = expanduser("~")
        f = home+"/.bashrc"
        print "[DEBUG]: establecer proxy en ", f
        try:
            fichero = open(f, "a")
            if (usuario):
                fichero.write("export HTTP_PROXY=\"http://%s:%s@%s:%s\"\n" % (usuario, clave, proxy, puerto))
                fichero.write("export HTTPS_PROXY=\"https://%s:%s@%s:%s\"\n" % (usuario, clave, proxy, puerto))
                fichero.write("export FTP_PROXY=\"ftp://%s:%s@%s:%s\"\n" % (usuario, clave, proxy, puerto))
            else:
                fichero.write("export HTTP_PROXY=\"http://%s:%s\"\n" % (proxy, puerto))
                fichero.write("export HTTPS_PROXY=\"https://%s:%s\"\n" % (proxy, puerto))
                fichero.write("export FTP_PROXY=\"ftp://%s:%s\"\n" % (proxy, puerto))

            fichero.write("export NO_PROXY=\"%s\"\n" % (noproxy))
            fichero.close()
        except Exception, e:
            print "[ERROR]:  except en pon_proxy_bashrc: %s" % e
            pass             
 
    # Desactivando el proxy para las aplicaciones de consola (.bashrc)    
    def quita_proxy_bashrc(self):
        home = expanduser("~")
        fichero = home + "/.bashrc"
        if (os.path.exists(fichero)):
            print "[DEBUG]: quitando proxy en ", fichero
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
            except Exception, e:
                print "[ERROR]:  except en quita_proxy_bashrc: %s" % e
                pass             

    # Escribe los parametros dados en el fichero /etc/apt/apt.conf
    # en caso de usar apt-add-repository es necesario usar root para ello hay que 
    # establecer el proxy para usuario root tambien (/etc/bash/bashrc)
    def pon_proxy_apt_conf(self, proxy, puerto, usuario, clave, noproxy):   
        home = expanduser("~")
        try:
            fichero1 = "/etc/apt/apt.conf"
            fichero2 = "apt.conf.temp"
            self.ficheros.append(fichero1)
            self.ficheros.append(fichero2)

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
            self.usarSudo = True # para modificar este fichero se necesitan permisos administrativos.
        except Exception, e:
            print "[ERROR]:  except en pon_proxy_apt_conf (apt): %s" % e
            pass             


        try:
            fichero1 = "/etc/bash.bashrc"
            fichero2 = "etc.bashrc.temp"
            self.ficheros.append(fichero1)
            self.ficheros.append(fichero2)
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
            f.write("export NO_PROXY=\"%s\"\n" % (noproxy))
            f.close()
            self.usarSudo = True # para modificar este fichero se necesitan permisos administrativos.
        except Exception, e:
            print "[ERROR]:  except en pon_proxy_apt_conf (bash): %s" % e
            pass             

    def quita_proxy_apt_conf(self):         
        print "[DEBUG]: quita_proxy_apt_conf"
        try:
            fichero1 = "/etc/apt/apt.conf"
            fichero2 = "apt.conf.temp"
            if (os.path.exists(fichero1)):
                copyfile(fichero1, fichero2)
                f = open(fichero2, "r")
                l = f.read()
                l2 = re.sub(r'\n?(.*Acquire::.*::proxy\s*".*"\;)', "", l)
                f.close()
                if (not l2 == l):
                    print "[DEBUG]: quitando proxy en ", fichero1
                    f = open(fichero2, 'w')
                    f.write(l2)
                    f.close()            
                    self.ficheros.append(fichero1)
                    self.ficheros.append(fichero2)
                    self.usarSudo = True # para modificar este fichero se necesitan permisos administrativos.
            

            fichero1 = "/etc/bash.bashrc"
            fichero2 = "etc.bashrc.temp"
            if (os.path.exists(fichero1)):
                copyfile(fichero1, fichero2 )
                f = open(fichero2, 'r')
                l = f.read()
                l2 = re.sub(r'\n?(.*_PROXY\s*=\s*".*")', "", l)
                f.close()
                # si el fichero original y el modificado son iguales no hacer nada
                if (not l2 == l):
                    print "[DEBUG]: quitando proxy en ", fichero1
                    f = open(fichero2, 'w')
                    f.write(l2)
                    f.close()
                    self.ficheros.append(fichero1)
                    self.ficheros.append(fichero2)
                    self.usarSudo = True # para modificar este fichero se necesitan permisos administrativos.

        except Exception, e:
            print "[ERROR]:  except en quita_proxy_apt_conf: %s" % e
            pass             

    # Escribe los parametros dados en el fichero ~/.gitconfig
    def pon_proxy_git(self, proxy, puerto, usuario, clave):   
        home = expanduser("~") 
        fich = home+"/.gitconfig"
        print "[DEBUG]: estableciendo proxy en ", fich
        config = ConfigParser.RawConfigParser()
        config.read(fich)
        valor='"http://'+ usuario + ':' + clave + '@' + proxy + ':' + puerto + '"'
        try:           
            if not config.has_section('http'):
                config.add_section('http')

            config.set('http', 'proxy', valor)
            with open(fich, 'wb') as configfile:
                config.write(configfile)
        except Exception, e:
            print "[ERROR]: PON_PROXY_GIT: %s" % e
            pass

    def quita_proxy_git(self):
        home = expanduser("~")
        fich = home+"/.gitconfig"
        if (os.path.exists(fich)):
            print "[DEBUG]: quitando proxy en ", fich
            config = ConfigParser.RawConfigParser()
            config.read(fich)

            try:
                config.remove_option("http", "proxy")
                with open(fich, 'wb') as configfile:
                    config.write(configfile)
            except Exception, e:
                print "[ERROR]: QUITA_PROXY_GIT: %s" % e
                pass

   # Activa el proxy para docker /etc/default/docker
    def pon_proxy_docker(self, proxy, puerto, usuario, clave, noproxy):        
        fichero1 = "/etc/default/docker"
        fichero2 = "docker.temp"
        print "[DEBUG]: estableciendo proxy en ", fichero1
        try:
            copyfile(fichero1, fichero2)
            f = open(fichero2, "a")
            if (usuario):
                f.write("export HTTP_PROXY=\"http://%s:%s@%s:%s\"\n" % (usuario, clave, proxy, puerto))
                f.write("export HTTPS_PROXY=\"https://%s:%s@%s:%s\"\n" % (usuario, clave, proxy, puerto))
            else:
                f.write("export HTTP_PROXY=\"http://%s:%s\"\n" % (proxy, puerto))
                f.write("export HTTPS_PROXY=\"https://%s:%s\"\n" % (proxy, puerto))

            f.write("export NO_PROXY=\"%s\"\n" % (noproxy))
            f.close()
            self.usarSudo = True # para modificar este fichero se necesitan permisos administrativos.            
            self.ficheros.append(fichero1)
            self.ficheros.append(fichero2)
        except Exception, e:
            print "[ERROR]:  except en pon_proxy_docker: %s" % e
            pass 

    # Desactivando el proxy para las aplicaciones de consola (.bashrc)    
    def quita_proxy_docker(self):
        fichero1 = "/etc/default/docker"
        fichero2 = "docker.temp"

        if (os.path.exists(fichero1)):    
            try:
                copyfile(fichero1, fichero2)
                f = open(fichero2, 'r')
                l = f.read()
                l2 = re.sub(r'\n?(.*_PROXY\s*=\s*["\'].*["\'])', "", l)
                f.close()
                # si el fichero original y el modificado son iguales no hacer nada 
                if (not l2 == l):
                    print "[DEBUG]: quitando proxy en ", fichero1
                    f = open(fichero2, 'w')
                    f.write(l2)
                    f.close()
                    self.usarSudo = True # para modificar este fichero se necesitan permisos administrativos.
                    self.ficheros.append(fichero1)
                    self.ficheros.append(fichero2)
               
            except Exception, e:
                print "[ERROR]:  except en quita_proxy_docker: %s" % e
                pass

if __name__ == "__main__":
    indicator = IndicadorProxy()
    gtk.main()

