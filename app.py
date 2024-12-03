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
import platform
import ctypes
import threading
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
    # progress bar
    progress_bar_height = 4
    progress_bar_width = 10

    # Add default transparency value
    DEFAULT_ALPHA = 0.2  # 50% transparent
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
        
        # Center the window on the screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculate position to center the window
        x = (screen_width // 2) - (self.windowSize // 2)
        y = (screen_height // 2) - (self.windowSize // 2)

        # Set the window geometry
        self.root.geometry(f"{self.windowSize}x{self.windowSize}+{x}+{y}")

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
        
        # Load and resize the image and convert it to ImageTk object to use in tkinter
        self.img, pil_img = self.load_image_from_url(self.current_track['album_art'])
        # self.img = ImageTk.PhotoImage(Image.open(self.defaultImg).resize(self.resizeTuple))  
        
        self.canvasCreateImage = self.canvas.create_image(int(self.windowSize/2), int(self.windowSize/2), image=self.img)

        # Add a more visible green bar at the bottom
        self.canvas.create_rectangle(
            0,  # x1 (left)
            self.windowSize - self.progress_bar_height,  # y1 (15 pixels from bottom)
            self.progress_bar_width,  # x2 (full width)
            self.windowSize,  # y2 (bottom)
            fill="#00FF00",  # Bright green color
            outline="",  # No outline
            width=0,
            tags="top"  # Ensure it stays on top
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
        self.ensure_taskbar_visibility()
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

    # Window Movement Conrtols & Helper

    def ensure_taskbar_visibility(self):
        os_name = platform.system()

        if os_name == "Windows":
            # Make it appear in the taskbar
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            ctypes.windll.user32.SetWindowLongW(hwnd, -8, hwnd)  # Set owner to null
            self.root.iconify()
            self.root.update_idletasks()
            self.root.deiconify()

        elif os_name == "Linux":
            # Some Linux desktop environments may require setting `_NET_WM_STATE`
            self.root.attributes("-type", "dialog")  # Adds taskbar visibility on some DEs

        elif os_name == "Darwin":  # MacOS
            # Use Tkinter's built-in `-fullscreen` attribute for taskbar compatibility
            self.root.attributes("-fullscreen", False)
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
    def get_dominant_color(self, img):
        """Extract the dominant color from the image."""
        img = img.convert("RGB")
        img = img.resize((50, 50))  # Resize for faster processing
        colors = img.getcolors(50*50)  # Get colors
        most_frequent_color = max(colors, key=lambda item: item[0])[1]  # Get the most frequent color
        return f'#{most_frequent_color[0]:02x}{most_frequent_color[1]:02x}{most_frequent_color[2]:02x}'
    
    def updateWindowUi(self):
        self.img, pil_img = self.load_image_from_url(self.current_track['album_art'])    
        self.canvasCreateImage = self.canvas.create_image(int(self.windowSize/2), int(self.windowSize/2), image=self.img)
        self.canvas.itemconfigure(self.canvasCreateImage, image=self.img)
        self.canvas.create_rectangle(
            0,  # x1 (left)
            self.windowSize - self.progress_bar_height,  # y1 (15 pixels from bottom)
            self.progress_bar_width,  # x2 (full width)
            self.windowSize,  # y2 (bottom)
            fill="#00FF00",  # Keep the color static green
            outline="",  # No outline
            width=0,
            tags="top"  # Ensure it stays on top
        )
        # Remove the color changing logic
        # The progress bar will remain green

    def check_track_updates(self):
        """Monitor for track changes and update UI accordingly in a separate thread"""
        def track_update_thread():
            try:
                current = self.spotplayer.get_current_track()
                if not current:
                    self._last_track_id = None
                    return
                
                current_id = f"{current['artist']}:{current['name']}"
                
                # Update the progress bar
                progress_percent = current['progress'] / current['duration']
                self.progress_bar_width = int(self.windowSize * progress_percent)
                
                # Redraw the green bar to new width
                self.canvas.create_rectangle(
                    0,  # x1 (left)
                    self.windowSize - self.progress_bar_height,  # y1 (15 pixels from bottom)
                    self.progress_bar_width,  # x2 (full width)
                    self.windowSize,  # y2 (bottom)
                    fill="#00FF00",  # Keep the color static green
                    outline="",  # No outline
                    width=0,
                    tags="top"  # Ensure it stays on top
                )
                
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
                self.root.after(self._update_interval, lambda: threading.Thread(target=track_update_thread).start())
        # Start the first thread
        threading.Thread(target=track_update_thread).start()
    
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

    def load_image_from_url(self, url: str) -> (tk.PhotoImage, Image.Image):
        size = (200, 200)
        if not url:
            img = Image.new('RGBA', size or (300, 300), (200, 200, 200, 255))
            return ImageTk.PhotoImage(img), img  # Return both PhotoImage and PIL Image

        try:
            response = requests.get(url, timeout=5)
            img = Image.open(BytesIO(response.content))
            if size:
                img = img.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img), img  # Return both PhotoImage and PIL Image
        except:
            img = Image.new('RGBA', size or (300, 300), (200, 200, 200, 255))
            return ImageTk.PhotoImage(img), img  # Return both PhotoImage and PIL Image

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
