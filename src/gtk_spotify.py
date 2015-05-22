from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository.GdkPixbuf import Pixbuf
import cgi
import dbus
import os
import urllib2
import json
import sys
import signal

def signal_handler(signal, frame):
    print(' Saliendo...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class LabelWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Spotify Info GTK")
       	Gtk.Window.set_default_size(self,960,300) 
	Gtk.Window.set_resizable(self,False)
        Gtk.Window.set_size_request(self,960,300)
	Gtk.Window.set_name(self,'MyWindow')
	Gtk.Window.set_icon_from_file(self,self.get_resource_path('spotify-client.png'))
        self.window_is_fullscreen = False
        self.connect("key_press_event",self.on_key_press_event)


	#Variables de cache que uso luego	
	self.trackid = ''
	self.last_album_url = ''

	style_provider = Gtk.CssProvider()

	css = """
	#MyWindow {
	    background-color: #222326;
	    margin:0px;
	}

	#MyWindow GtkLabel {
            background-color: #222326;
	    color: #909298;
            font-size:38px;
	    margin:0px;
	    padding:0px;
        }
	#MyWindow GtkLabel:first-child {
	    color:#84bd00;
	}
	#MyWindow GtkBox {
            background-color: #222326;
            margin:0px;
        }
	"""

	style_provider.load_from_data(css)

	Gtk.StyleContext.add_provider_for_screen(
	    Gdk.Screen.get_default(), 
	    style_provider,     
	    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
	)
	#Creo el los contenedores
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_homogeneous(False)
	
	#Creo los labels
	self.label_title = Gtk.Label()
	self.label_title.set_justify(Gtk.Justification.LEFT)
	self.label_title.set_use_markup(True)
        box.pack_start(self.label_title, False, False, 20)

	self.label_artist = Gtk.Label()
        self.label_artist.set_use_markup(True)
        box.pack_start(self.label_artist, False, False, 20)

	self.label_album = Gtk.Label()
        self.label_album.set_use_markup(True)
        box.pack_start(self.label_album, False, False, 20)

	self.image = Gtk.Image()
	box.pack_start(self.image, False, False, 20)
	#Agrego el box a la ventana
        self.add(box)
	
	#Fuerzo a que traiga la info de dbus
	self.timeout()

	#Agrego un timer para que refresque cada 500 milisegundos
	GObject.timeout_add(500, self.timeout)

	
    def get_spotify(self):
	bus = dbus.SessionBus()
        proxy = bus.get_object('org.mpris.MediaPlayer2.spotify', '/org/mpris/MediaPlayer2')
        interface = dbus.Interface(proxy, 'org.mpris.MediaPlayer2.Player')
        props_iface = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
	reply = props_iface.GetAll("org.mpris.MediaPlayer2.Player")
	return reply

    def timeout(self):
	#Obtengo la informacion de la aplicacion mediante dbus
	reply = self.get_spotify()
	trackid = reply['Metadata']['xesam:url'].split(':')[2]

	#Solo si cambio de track vuelvo a bajar la tapa del disco
	if trackid != self.trackid:
	    self.trackid = trackid
	    url = 'https://api.spotify.com/v1/tracks/' + self.trackid
	    data = json.load(urllib2.urlopen(url))
	    url = data['album']['images'][0]['url']	  
	    #Solo si cambio de disco bajo la tapa
	    if self.last_album_url != url:
		self.last_album_url = url
	        print('Bajando imagen del album: ' + url)
	        response = urllib2.urlopen(url)
	        fname = url.split("/")[-1]
	        f = open('/tmp/'+fname, "wb")
	        f.write(response.read())
	        f.close()
	        response.close()
	        self.image.set_from_pixbuf(Pixbuf.new_from_file('/tmp/'+fname))
	        self.image.show() 
	
	title = reply['Metadata']['xesam:title']
	artist = reply['Metadata']['xesam:artist'][0]
	album = reply['Metadata']['xesam:album']
    
        #Trunco el tema si es muy largo
        title = title[:32] + (title[32:] and ' ...')

	#Escapo caracteres raros
	artist = cgi.escape(artist)
        artist = artist[:32] + (artist[32:] and ' ...')

	album = cgi.escape(album)
        album = album[:32] + (album[32:] and ' ...')

        artist = '<i><small><span color="white">ARTIST: </span></small></i>' + artist
        album = '<i><small><span color="white">ALBUM: </span></small></i>' + album

	self.label_title.set_text(title)
	self.label_artist.set_markup(artist)
	self.label_album.set_markup(album)

	return True

    def get_resource_path(self,rel_path):
        dir_of_py_file = os.path.dirname(__file__)
	rel_path_to_resource = os.path.join(dir_of_py_file, rel_path)
	abs_path_to_resource = os.path.abspath(rel_path_to_resource)
	return abs_path_to_resource

    def toggle_full(self):
        if not self.window_is_fullscreen:
            Gtk.Window.fullscreen(self)
            self.window_is_fullscreen = True
        else:
            Gtk.Window.unfullscreen(self)
            self.window_is_fullscreen = False

    def on_key_press_event(self, widget, event, user_data=None):
        key = Gdk.keyval_name(event.keyval)
        if key == "F11":
              self.toggle_full()
              return True
        return False


window = LabelWindow()        
window.connect("delete-event", Gtk.main_quit)
window.show_all()
Gtk.main()
