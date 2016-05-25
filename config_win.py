#!/usr/bin/python
# -*- coding: latin-1 -*-
from gi.repository import Gtk as gtk
from gi.repository import Gio 
from gi.repository import GLib 
import ConfigParser
import os
import sys

class ConfigWin:
    def __init__(self):
    
        #Init Glade Builder
        builder = gtk.Builder()
        
        ficherin = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'indicador-proxy.glade')
        builder.add_from_file(ficherin)
        
        # fichero de configuración
        self.config_file = os.getenv("HOME")+'/.config/indicador-proxy/config.ini'
        self.config = ConfigParser.RawConfigParser()

        #Connect signals to builder
        self.window = builder.get_object('window1')
        builder.connect_signals(self)

        # Get components from builder
        self.servidor = builder.get_object('te_servidor')
        self.puerto   = builder.get_object('te_puerto')
        self.aut      = builder.get_object('cb_aut')
        self.usuario  = builder.get_object('te_usuario')
        self.clave    = builder.get_object('te_clave')
        self.clave    = builder.get_object('te_clave')
        self.apt      = builder.get_object('cb_apt')
        self.excep    = builder.get_object('te_excep')

        #muestra la configuracion
        gs_proxy = Gio.Settings.new('org.gnome.system.proxy')
        gs_proxy_http = Gio.Settings.new('org.gnome.system.proxy.http')
        self.servidor.set_text(gs_proxy_http.get_string('host'))
        self.puerto.set_text(str(gs_proxy_http.get_int('port')))
        self.usuario.set_text(gs_proxy_http.get_string('authentication-user'))
        self.clave.set_text(gs_proxy_http.get_string('authentication-password'))

        lista_excepciones=gs_proxy.get_value('ignore-hosts')
        lexcep=""
        for e in lista_excepciones:
            lexcep+=e+","
        lexcep=lexcep[:-1]
        self.excep.set_text(lexcep)

        self.aut.set_active(gs_proxy_http.get_boolean('use-authentication'))
        self.apt.set_active(self.lee_conf_apt())

    def show(self):
        self.window.show()

    def lee_conf_apt(self, clave="proxy_apt"):
        print "[DEBUG] leyendo fichero de configuración"
        retorno = False
        self.config.read(self.config_file)
        if self.config.get('Configuracion', clave) == 'True':
            retorno = True
        return retorno

    def escribe_conf_apt(self, clave, valor):
        print "[DEBUG] Escribiendo en el fichero de  configuración ", clave, valor
        self.config.set('Configuracion', clave, valor)
        with open(self.config_file, 'wb') as configfile:
            self.config.write(configfile)


    def b_aceptar_clicked(self, button):
        print ("[DEBUG] Boton aceptar")
        global Glib

        gs_proxy = Gio.Settings.new('org.gnome.system.proxy')
        cadena=""
        lista=""
        lista=self.excep.get_text().split(",")
#       for e in lista:
#           print "-", e
#           cadena+="'"+e.strip()+"',"
#       cadena=cadena[:-1]
#       print "texto recogido", cadena
#       a = array(lista)
#       print "array", a

#GLib.Variant('as', ['string1', 'string2']))
        gs_proxy.set_value('ignore-hosts', GLib.Variant('as',lista))


        gs_proxy_http = Gio.Settings.new('org.gnome.system.proxy.http')
        gs_proxy_http.set_string('host', self.servidor.get_text())
        gs_proxy_http.set_int('port', int(self.puerto.get_text()))
        gs_proxy_http.set_boolean('use-authentication', self.aut.get_active())
        gs_proxy_http.set_string('authentication-user',  self.usuario.get_text())
        gs_proxy_http.set_string('authentication-password', self.clave.get_text())
        gs_proxy_http.set_boolean('enabled',  'true')

        self.window.destroy()

    def b_cancelar_clicked(self, button):
        print ("[DEBUG] Boton cancelar")
        self.window.destroy()

    def cb_aut_toggled(self, button):
        # disable user/pwd fields   
        value = button.get_active()
        print ("[DEBUG]: AUTH pulsado (" + str(value) +")")
        self.usuario.set_sensitive(value)
        self.clave.set_sensitive(value)

    def cb_apt_toggled(self, button):
        # use proxy with apt-get 
        value = button.get_active()
        print ("[DEBUG]: APT-GET pulsado (" + str(value) +")")
        self.escribe_conf_apt("proxy_apt", value)

           
            
            
            
