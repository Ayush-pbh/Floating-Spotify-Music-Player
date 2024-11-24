# IMPORTS
from spotify_controller import SpotifyController
import threading
from PIL import Image, ImageTk
import tkinter as tk
from mutagen.id3 import ID3
from subprocess import call  # for volume controlls
import requests
from io import BytesIO
import os
from dotenv import load_dotenv
load_dotenv()
# Custom Class Imports
# from player import Player


# UI for the application
class App(threading.Thread):
    # VARIABLES
   
    windowSize = 200
    GWL_EXSTYLE = -20
    WS_EX_APPWINDOW = 0x00040000
    WS_EX_TOOLWINDOW = 0x00000080
    resizeTuple = (windowSize, windowSize)

    r = windowSize
    defaultImg = "./default.jpg"
    toSetImg = "./default.jpg"
    voll = 50
    didmovelasttime = False
    # Add default transparency value
    DEFAULT_ALPHA = 0.8  # 50% transparent
    HOVER_ALPHA = 1.0    # 100% opaque on hover
    current_track = None
    # Track monitoring variables
    _last_track_id = None
    _update_interval = 1000  # Check every second

    def run(self):
        print("[i] APP STARTED ✅")
        # Initilize Spotify
        # Initialize the controller
        self.spotplayer = SpotifyController(client_id=os.getenv('CLIENTID'), client_secret=os.getenv('CLIENTSECRET'), redirect_uri=os.getenv('REDIRECTURI'))

        self.current_track = self.spotplayer.get_current_track()
        self.main()

    def set_appwindow(self, root):
        root.wm_withdraw()
        root.after(10, lambda: root.wm_deiconify())

    def main(self):
        self.root = tk.Tk()
        self.root.wm_title("Floating Spotify")
        self.root.maxsize(self.windowSize, self.windowSize)
        self.root.title("Floating Spotify")
        # Set initial transparency
        self.root.attributes('-alpha', self.DEFAULT_ALPHA)
        
        # making icon
        
        self.icon = tk.PhotoImage('./icon.png')
        self.root.iconphoto(False, self.icon)
        # making canvas
        self.canvas = tk.Canvas(
            self.root,
            width=self.windowSize,
            height=self.windowSize,
            highlightthickness=0,
        )
        
        # Event Listeners

        # Add mouse enter/leave events for transparency
        self.root.bind('<Enter>', self.on_hover)
        self.root.bind('<Leave>', self.on_leave)

        # Right Click to open popup!
        self.canvas.bind("<Button-3>", self.do_popup)
        
        # Double Left Click to toggle play pause
        self.canvas.bind("<Double-1>", self.spotplayer.toggle_playback)
        self.canvas.pack()

        # Load and resize the image and convert it to ImageTk object to use in tkinter
        self.img = self.load_image_from_url(self.current_track['album_art'])
        # self.img = ImageTk.PhotoImage(Image.open(self.defaultImg).resize(self.resizeTuple))  
        
        self.canvasCreateImage = self.canvas.create_image(int(self.windowSize/2), int(self.windowSize/2), image=self.img)

        # Menu
        self.m = tk.Menu(self.root, tearoff=0)
        self.m.add_command(label="Next", command=self.NextSong)
        self.m.add_command(label="Prev", command=self.spotplayer.previous_track)
        self.m.add_command(label="Shuffle", command=self.spotplayer.toggle_shuffle)

        self.m.add_command(label="Stop", command=print('[stop]'))
        self.m.add_separator()
        self.m.add_command(label="Close", command=self.QuitProgram)
        
        # Volume Controls using mousewheel
        self.canvas.bind("<Button-4>", self.volume)
        self.canvas.bind("<Button-5>", self.volume)
        
        # remove window borders
        self.root.overrideredirect(True)  
        self.root.after(10, lambda: self.set_appwindow(self.root))
        
        # making it dragable
        self.canvas.bind("<Button-1>", self.start_move)
        self.canvas.bind("<Left>", self.keys)
        self.canvas.bind("<ButtonRelease-1>", self.stop_move)
        self.canvas.bind("<B1-Motion>", self.do_move)

        # Check for track changes
        self.check_track_updates()
        # the mainloop
        self.root.mainloop()

    # Window Movement Conrtols & Helpers
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
        self.canimove = True
        self.didmovelasttime = False

    def stop_move(self, event):
        self.x = None
        self.y = None
        # self.canimove = False
        # if not self.didmovelasttime:
        #     player.PrevSong()

    def do_move(self, event):
        # if not self.canimove:
        #     return
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
        # self.didmovelasttime = True
    def on_hover(self, event):
        """Make window opaque when mouse hovers over it"""
        self.root.attributes('-alpha', self.HOVER_ALPHA)

    def on_leave(self, event):
        """Make window semi-transparent when mouse leaves"""
        self.root.attributes('-alpha', self.DEFAULT_ALPHA)

    def QuitProgram(self):
        self.root.quit()
        print("Quitting Program")

    def do_popup(self, event):
        try:
            self.m.tk_popup(event.x_root, event.y_root)
        finally:
            self.m.grab_release()

    def keys(self, event):
        print("Left Working!")

    def updateWindowUi(self):
        self.img = self.load_image_from_url(self.current_track['album_art'])    
        self.canvasCreateImage = self.canvas.create_image(int(self.windowSize/2), int(self.windowSize/2), image=self.img)
        self.canvas.itemconfigure(self.canvasCreateImage, image=self.img)
    
    def check_track_updates(self):
        """Monitor for track changes and update UI accordingly"""
        try:
            current = self.spotplayer.get_current_track()
            if not current:
                self._last_track_id = None
                return
            
            current_id = f"{current['artist']}:{current['name']}"
            
            # Detect track change
            if self._last_track_id != current_id:
                print(f"Track changed: {current['name']} by {current['artist']}")
                self._last_track_id = current_id
                self.updateCurrentTrack()
                self.updateWindowUi()
        except Exception as e:
            print(f"Error checking track updates: {e}")
        finally:
            # Schedule next check
            self.root.after(self._update_interval, self.check_track_updates)
    
    
    # Music Control Functions & Helpers

    def updateCurrentTrack(self):
        self.current_track = self.spotplayer.get_current_track()

    
    def NextSong(self):
        print('[next-song]')
        self.spotplayer.next_track()
        self.updateCurrentTrack()
        self.updateWindowUi()
        
    def volume(self, event):
        i = event.num
        # change 5 to 4 if want to reverse the scroll-volume behaviour!
        if i == 5:
            # i is +ive i.e increase volume...
            self.spotplayer.change_volume(True)
        else:
            self.spotplayer.change_volume(False)


    def AlbumArtChanger(self):
        # This fucntion changes the image of the canvass to the current default image this
        # function assumnes that the calling fuction has already changed the value of the self.toSetImg
        # to the current wanted Image.
        self.img = self.toSetImg
        self.canvas.itemconfigure(self.canvasCreateImage, image=self.img)

    def load_image_from_url(self, url: str) -> tk.PhotoImage:
        size=(200,200)
        if not url:
            return ImageTk.PhotoImage(Image.new('RGBA', size or (300, 300), (200, 200, 200, 255)))
            
        try:
            response = requests.get(url, timeout=5)
            img = Image.open(BytesIO(response.content))
            if size:
                img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except:
            return ImageTk.PhotoImage(Image.new('RGBA', size or (300, 300), (200, 200, 200, 255)))

    def getRawImage(self, addr):
        img_name = addr
        #print('Image is :>'+img_name)
        img = ID3(img_name)
        #print('getting albumart for: '+img_name)
        datab = ''
        try:
            datab = img['APIC:'].data
        except:
            try:
                datab = img['APIC:3.jpeg'].data
            except:
                try:
                    datab = img['APIC:FRONT_COVER'].data
                except:
                    try:
                        datab = img['APIC:"Album cover"'].data
                    except:
                        try:
                            datab = img['APIC:3.png'].data
                        except:
                            datab = './logo.jpg'
        return io.BytesIO(datab)

app = App()
app.start()