import random
import threading
import vlc
import os
import tkinter as tk
from tkinter import filedialog
from mutagen.id3 import ID3

class Player(threading.Thread):

    playable_list=[]
    folder = ''
    Playing = False
    Stopped = True
    index = 0
    MusicEnd = 0
    # def SongEnd(self, event):
    #     print("Next Song")
    #     if self.index < len(self.playable_list) - 1:
    #         self.NextSong()
    #         print("Next Song P")
    #     else:
    #         print("Playlist has ended")

    def run(self):
        self.instance = vlc.Instance()
        self.vlcplayer = vlc.MediaListPlayer()
        def sngend(e):
            print(f"Next Song Is On!!! {self.instance.medial} : {self.playable_list[self.index]}")
        print(dir(vlc.EventType))
        self.vlcplayer.event_manager().event_attach(vlc.EventType.MediaListPlayerNextItemSet, sngend)
        
        self.mediaList = self.instance.media_list_new()
        
        self.ScanFolder()
        self.Play(0)
        
    def Play(self,index):

        self.vlcplayer.play_item_at_index(index)
        print('Playing :',self.playable_list[index])
        self.Playing = True
        self.index = index
        self.Stopped = False


    def shufflePlaylist(self):
        input_list = self.playable_list
        if not input_list:
            return []  # Return an empty list if the input list is empty

        shuffled_list = input_list.copy()  # Create a copy to avoid modifying the original list
        random.shuffle(shuffled_list)  # Shuffle the copy in place
        self.playable_list =  shuffled_list
    
    

    def NextSong(self):
        # self.index += 1
        # self.Play(self.index)
        self.vlcplayer.next()
        self.index += 1

    def PrevSong(self):
        if self.index !=0:
            self.vlcplayer.previous()
            self.index -= 1

        else:
            print("No Prev song!")

    def Pause(self):
        self.vlcplayer.pause()
        self.Playing = False

    def Unpause(self):
        self.vlcplayer.play()
        self.Playing = True

    def Stop(self):
        self.vlcplayer.stop()
        self.isPlaying = False
        self.Stopped = True
    
    def Toggle(self,event):
        if self.Stopped:
            self.Play(self.index)
            return
        if self.Playing:
            self.Pause()
        else:
            self.Unpause()

    def printList(self):
        for item in self.playable_list:
            print(item)
    

    def getSongsLocationFromUser(self):
        # Ask user for his music folder location
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        # Open a file/folder picker dialog and set the title
        folder_path = filedialog.askdirectory(title="Select Your Preferred Music Folder")
        # write that folderpath to src.txt
        writefile = open('src.txt', 'w')
        writefile.write(folder_path)

    def ScanFolder(self):
        try:
            # Try opening the src.txt file
            fp = open('src.txt','r')
        except:
            # Ask user for his music folder
            print("No src.txt found! Asking User for folder!")
            self.getSongsLocationFromUser()
            # read the src.txt again!
            fp = open('src.txt','r')

        #read from the src.txt
        text = fp.read()
        fp.close()
        
        self.folder  = text

        if not self.folder.endswith('/'):
            # Add a trailing / at the end of the folderpath
            self.folder+='/'

        # Scan for music in the folder *currently only mp3 supported.
        for item in os.listdir(self.folder):
            if item.endswith('.mp3'):
                self.playable_list.append(item)
                self.mediaList.add_media(self.instance.media_new(self.folder + item))
        self.vlcplayer.set_media_list(self.mediaList)
        print(self.mediaList)
        

        print("Folder Scan Complete!", len(self.playable_list), "Songs Found!")

    
