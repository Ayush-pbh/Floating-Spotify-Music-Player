# IMPORTS
import threading
from PIL import Image, ImageTk
import tkinter as tk
from mutagen.id3 import ID3
from subprocess import call  # for volume controlls

# Custom Class Imports
# from player import Player


# UI for the application
class App(threading.Thread):
    # VARIABLES
    # WINDOW SIZE :
    windowSize = 100
    GWL_EXSTYLE = -20
    WS_EX_APPWINDOW = 0x00040000
    WS_EX_TOOLWINDOW = 0x00000080
    resizeTuple = (windowSize, windowSize)

    r = windowSize
    defaultImg = "./default.jpg"
    toSetImg = "./default.jpg"
    voll = 50
    didmovelasttime = False

    def run(self):
        print("[ APP STARTED ]")
        # self.player = Player()
        # self.player.start()
        self.main()

    def set_appwindow(self, root):
        root.wm_withdraw()
        root.after(10, lambda: root.wm_deiconify())

    def main(self):
        self.root = tk.Tk()
        self.root.wm_title("FMP")
        self.root.maxsize(
            self.windowSize, self.windowSize
        )  # only one fixed size from version 2 and above.
        self.root.title("FMP")

        # making icon
        self.icon = tk.PhotoImage(file="./icon.png")
        self.root.iconphoto(False, self.icon)
        # making canvas
        self.canvas = tk.Canvas(
            self.root,
            width=self.windowSize,
            height=self.windowSize,
            highlightthickness=0,
        )

        # Right Click to open popup!
        self.canvas.bind("<Button-3>", self.do_popup)
        # Double Left Click to toggle play pause
        self.canvas.bind("<Double-1>", print("[play/pause]"))
        self.canvas.pack()

        self.img = ImageTk.PhotoImage(
            Image.open(self.defaultImg).resize(self.resizeTuple)
        )  # the one-liner I used in my app
        self.canvasCreateImage = self.canvas.create_image(int(self.windowSize/2), int(self.windowSize/2), image=self.img)

        # Menu
        self.m = tk.Menu(self.root, tearoff=0)
        self.m.add_command(label="Next", command=self.NextSong)
        self.m.add_command(label="Prev", command=print("[prev-song]"))
        self.m.add_command(label="Shuffle", command=print('[shuffle-playlist]'))

        self.m.add_command(label="Stop", command=print('[stop]'))
        self.m.add_separator()
        self.m.add_command(label="Close", command=self.QuitProgram)

        self.root.overrideredirect(True)  # remove window borders
        self.root.after(10, lambda: self.set_appwindow(self.root))

        # making it dragable
        self.canvas.bind("<Button-1>", self.start_move)
        self.canvas.bind("<Left>", self.keys)
        self.canvas.bind("<Button-4>", self.volume)
        self.canvas.bind("<Button-5>", self.volume)
        self.canvas.bind("<ButtonRelease-1>", self.stop_move)
        self.canvas.bind("<B1-Motion>", self.do_move)

        # the mainloop
        self.root.mainloop()
    
    def NextSong(self):
        print('[next-song]')
        

    def QuitProgram(self):
        self.root.quit()
        print("Quitting Program")

    def volume(self, event):
        i = event.num
        # change 5 to 4 if want to reverse the scroll-volume behaviour!
        if i == 5:
            # i is +ive i.e increase volume...
            if self.voll >= 100:
                # volume already full
                return 0
            else:
                self.voll = self.voll + 1
                a = call(["amixer", "-D", "pulse", "sset", "Master", f"{self.voll}%"])
        else:
            # i is -ve i.e decrease volume
            if self.voll <= 0:
                # no more decrase...
                return 0
            else:
                self.voll = self.voll - 1
                a = call(["amixer", "-D", "pulse", "sset", "Master", f"{self.voll}%"])

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

    def AlbumArtChanger(self):
        # This fucntion changes the image of the canvass to the current default image this
        # function assumnes that the calling fuction has already changed the value of the self.toSetImg
        # to the current wanted Image.
        self.img = self.toSetImg
        self.canvas.itemconfigure(self.canvasCreateImage, image=self.img)

    def do_popup(self, event):
        try:
            self.m.tk_popup(event.x_root, event.y_root)
        finally:
            self.m.grab_release()

    def keys(self, event):
        print("Left Working!")

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
