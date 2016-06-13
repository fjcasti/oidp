#!/usr/bin/python
# -*- coding: latin-1 -*-
from gi.repository import Gtk as gtk
from gi.repository import Gio 
from gi.repository import GLib 
import ConfigParser
from propiedades import  Propiedades
from registro import Registro
import os
import sys

class ConfigWin:
    # variables de clase
    objPropiedades = None
    objRegistro = None

    def __init__(self):

        #Init Glade Builder
        builder = gtk.Builder()
        ficherin = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'indicador-proxy.glade')
        builder.add_from_file(ficherin)
        
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
        self.git      = builder.get_object('cb_git')
        self.docker   = builder.get_object('cb_docker')

        # fichero de configuración
        self.objPropiedades = Propiedades()
        # acceso al registro
        self.objRegistro = Registro()

        # muestra la configuracion. Rellenamos los campos
        self.servidor.set_text(self.objRegistro.getHost())
        self.puerto.set_text(self.objRegistro.getPort())
        self.usuario.set_text(self.objRegistro.getUser())
        self.clave.set_text(self.objRegistro.getPassword())
        self.excep.set_text(self.objRegistro.getIgnoreList())
        self.aut.set_active(self.objRegistro.getAuthentication())
        
        a=self.objPropiedades.lee("proxy_apt")
        b=self.objPropiedades.lee("proxy_git")
        c=self.objPropiedades.lee("proxy_docker")
        self.apt.set_active(False)
        self.git.set_active(False)
        self.docker.set_active(False)
        if (a == "True"):
            self.apt.set_active(True)

        if (b == "True"):
            self.git.set_active(True)

        if (c == "True"):
            self.docker.set_active(True)


    def show(self):
        self.window.show()

    def b_aceptar_clicked(self, button):
        self.objRegistro.setIgnoreList(self.excep.get_text())
        self.objRegistro.setHost(self.servidor.get_text())
        self.objRegistro.setPort(self.puerto.get_text())
        self.objRegistro.setAuthentication(self.aut.get_active())
        self.objRegistro.setUser(self.usuario.get_text())
        self.objRegistro.setPassword(self.clave.get_text())

        value = self.apt.get_active()
        self.objPropiedades.escribe("proxy_apt", str(value))
        value = self.git.get_active()
        self.objPropiedades.escribe("proxy_git", str(value))
        value = self.docker.get_active()
        self.objPropiedades.escribe("proxy_docker", str(value))


        self.window.destroy()

    def b_cancelar_clicked(self, button):
        self.window.destroy()

    def cb_aut_toggled(self, button):
        value = button.get_active()
        self.usuario.set_sensitive(value)
        self.clave.set_sensitive(value)

    def cb_apt_toggled(self, button):
        value = button.get_active()

    def cb_git_toggled(self, button):
        value = button.get_active()

    def cb_docker_toggled(self, button):
        value = button.get_active()
