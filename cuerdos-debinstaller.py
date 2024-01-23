import gi
import subprocess
import os
import threading

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

class DebInstaller(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="DEB package installer")
        self.set_default_size(400, 300)

        # Crear un contenedor
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(container)

        # Crear un ScrolledWindow
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        container.pack_start(scrolled_window, True, True, 0)

        # Crear un TextView no editable
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.NONE)  # Desactivar el ajuste de línea
        scrolled_window.add(self.textview)

        # Crear un botón para iniciar la instalación
        install_button = Gtk.Button(label="Install DEB package")
        install_button.connect("clicked", self.on_install_button_clicked)
        container.pack_start(install_button, False, False, 0)

    def on_install_button_clicked(self, button):
        # Crear un diálogo de selección de archivos
        dialog = Gtk.FileChooserDialog(
            title="Select a DEB package",
            action=Gtk.FileChooserAction.OPEN,
        )

        filter_deb = Gtk.FileFilter()
        filter_deb.set_name("DEB packages")
        filter_deb.add_mime_type("application/vnd.debian.binary-package")
        dialog.add_filter(filter_deb)

        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            deb_file_path = dialog.get_filename()
            
            # Ejecutar el comando en un hilo separado
            install_thread = threading.Thread(target=self.install_deb, args=(deb_file_path,))
            install_thread.start()
            
        dialog.destroy()

    def install_deb(self, deb_file_path):
        try:
            # Utilizar pkexec para ejecutar un script de shell que agrupa los comandos
            script = f"#!/bin/bash\n\ndpkg -i {deb_file_path}\napt-get install -f -y"
            script_path = self.create_temp_script(script)

            pkexec_command = f"pkexec {script_path}"
            self.run_command(pkexec_command)
        except Exception as e:
            self.append_text(f"Error: {str(e)}")

    def create_temp_script(self, script_content):
        script_path = "/tmp/deb_installer_script.sh"
        with open(script_path, "w") as script_file:
            script_file.write(script_content)
        os.chmod(script_path, 0o755)  # Make the script executable
        return script_path

    def run_command(self, command):
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Leer la salida del comando
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                GLib.idle_add(self.append_text, line)

            # Leer la salida de error del comando
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                GLib.idle_add(self.append_text, line)

            # Esperar a que el comando termine
            process.wait()
        except Exception as e:
            self.append_text(f"Error: {str(e)}")

    def append_text(self, text):
        buffer = self.textview.get_buffer()
        end_iter = buffer.get_end_iter()
        buffer.insert(end_iter, text)
        
        # Obtener el iterador de inicio
        start_iter = buffer.get_start_iter()
        
        # Hacer scroll hacia el final del texto
        self.textview.scroll_to_iter(end_iter, 0.0, False, 0.0, 0.0)

win = DebInstaller()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
