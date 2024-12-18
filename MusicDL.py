from pytubefix import Playlist, YouTube
from pytubefix.innertube import _default_clients
import eyed3
from eyed3.core import Date
from requests import get
import numpy as np
import cv2
from pydub import AudioSegment
from mutagen.id3 import ID3, APIC
import os
from threading import Thread
import asyncio
from time import sleep
from ytmusicapi import YTMusic



class ArtistDL:
    def __init__(
self,
ArtistID    : str,
Path        : str = './Music/[Artist]/[Album]/[SongNum] - [SongName]',
APIinstance : YTMusic = YTMusic(),
ThreadCap   : int = 3
):
        self.ArtistID = ArtistID
        self.Path = Path
        
        self.type = ArtistDL
        
        self.ThreadCap = ThreadCap
        self.CurrentInfo = []
        
        self.API = APIinstance
        self.ArtistData = self.API.get_artist(self.ArtistID)
        self.ArtistName = self.ArtistData['name']
        
        self.Albums  : list = self.ArtistData['albums']['results'] if 'albums' in self.ArtistData.keys() else []
        self.Singles : list = self.ArtistData['singles']['results'] if 'singles' in self.ArtistData.keys() else []
        
        self.threads : list[Thread]     = []
        self.objects : list[PlaylistDL] = []
        
        
    def Download(self):
        # Albums: dict_keys(['title', 'type', 'artists', 
        # 'browseId', 'audioPlaylistId', 'thumbnails', 
        # 'isExplicit', 'year'])
        # Singles: dict_keys(['title', 'year', 'browseId', 
        # 'thumbnails'])
        #
        
        
        
        for i in self.Albums:
            
            APIData = self.API.get_album(i['browseId'])
            
            obj = PlaylistDL(
            PlaylistID  = i['audioPlaylistId'],
            Path        = self.Path,
            APIinstance = self.API,
            APIData     = APIData,
            PLData      = Playlist('https://youtube.com/playlist?id='+APIData['audioPlaylistId']),
            AlbumArtist=self.ArtistName
            )
            
            self.objects.append(obj)
            
            indx = self.objects.index(obj)
            
            thr = Thread(target=self.objects[indx].Download,name=APIData['title'])
            
            self.threads.append(thr)
        
        for i in self.Singles:
            
            PAData = self.API.get_album(i['browseId'])
            
            obj = PlaylistDL(
            PlaylistID  = PAData['audioPlaylistId'],
            Path        = self.Path,
            APIinstance = self.API,
            APIData     = PAData,
            PLData      = Playlist('https://youtube.com/playlist?id='+PAData['audioPlaylistId']),
            AlbumArtist=self.ArtistName
            )

            self.objects.append(obj)
            
            indx = self.objects.index(obj)
            
            thr = Thread(target=self.objects[indx].Download,name=PAData['title'])
            
            self.threads.append(thr)
    
    
        #Insert Start Threads/Data Extraction
        
        
        #[{"name":'album',"status":'0/100'}]
        
        
        self.running = True
        self.Update()
        

        
    def Update(self):
        print("Started Artist Update for: "+self.ArtistName)
        self.CurrentInfo = []
        
        self.running = True
        dlindx = -1
        
        while self.running:
            #Update Current Info
            self.CurrentInfo = []
            for obj in self.objects:
                indx = self.objects.index(obj)
                thr = self.threads[indx]
                
                status = 'Finished' if obj.CurrentNum > obj.TotalNum else 'Not Started'
                status = status if not thr.is_alive() else 'Running'
                cnum = obj.CurrentNum if obj.CurrentNum <= obj.TotalNum else obj.CurrentNum -1
                
                
                data = {"Name": obj.AlbumName, 
                        "Progress": f'{cnum}/{obj.TotalNum}',
                        "Status": status}
                self.CurrentInfo.append(data)
                
            #Start Downloads w/ async
            
            if dlindx == len(self.threads)-1:
                check = False
                for i in self.threads:
                    if i.is_alive():
                        check = True
                self.running = check
            elif dlindx == -1:
                for i in range(self.ThreadCap):
                    thr = self.threads[i]
                    
                    thr.start()
                    dlindx += 1
                    
            else:
                alive = 0
                for thr in self.threads:
                    if thr.is_alive():
                        alive += 1
                print("alive:",alive)
                if alive < self.ThreadCap:
                    for i in range(self.ThreadCap-alive):
                        dlindx += 1
                        thr = self.threads[dlindx]
                        print('Starting'+ self.objects[dlindx].AlbumName)
                        thr.start()
            
            
            sleep(5)

    
            

class PlaylistDL:
    def __init__(
self,
PlaylistID  : str,
Path        : str = './Music/[Artist]/[Album]/[SongNum] - [SongName]',
APIinstance : YTMusic = YTMusic(),
APIData     : dict | None = None,
PLData      : Playlist | None = None,
AlbumArtist : str | None = None
):
        self.Path = Path
        
        self.type = PlaylistDL
        
        self.API = APIinstance
        self.PlaylistID = PlaylistID
        self.BrowseID = str(self.API.get_album_browse_id(self.PlaylistID))
 
        
        if APIData != None:
            self.IsSubprocess = True
            self.PlaylistData = APIData
            self.Playlist = PLData if PLData != None else Playlist('https://youtube.com/playlist?id='+self.PlaylistID)
        else:
            self.IsSubprocess = False
            self.PlaylistData = YTMusic().get_album(self.BrowseID)
            self.Playlist = Playlist("https://youtube.com/playlist?list="+self.PlaylistID)
        
        c = 0
        for i in self.PlaylistData['thumbnails']:
            if i['width'] > c:
                self.AlbumCoverURL = i['url']
                c = i['width']
        
        
        self.AlbumName = self.PlaylistData['title']
        self.AlbumCover = get(self.AlbumCoverURL).content
        self.AlbumYear = self.PlaylistData['year']
        self.AlbumArtist = AlbumArtist if AlbumArtist != None else self.PlaylistData['artists'][0]['name']
        
        self.CurrentNum = 0
        self.TotalNum = len(self.PlaylistData['tracks'])

    def Download(self):
        PlaylistTimeout = 2
        
        self.Songs = self.Playlist.videos
        
        self.CurrentNum = 1
        while self.CurrentNum <= self.TotalNum:
            CurrentSong = self.Songs[self.CurrentNum-1]
            CurrentPLTData = self.PlaylistData['tracks'][self.CurrentNum-1]
            CurrentVideoData = self.API.get_song(CurrentPLTData['videoId'])['videoDetails']
            
            DLInstance = YoutubeDL(
                SongID      = CurrentVideoData['videoId'],
                Path        = self.Path,
                APIinstance = self.API,
                APIData     = CurrentVideoData,
                YTData      = CurrentSong,
                AlbumName   = self.AlbumName,
                AlbumYear   = self.AlbumYear,
                AlbumCover  = self.AlbumCover,
                AlbumArtist = self.AlbumArtist,
                SongNum     = str(self.CurrentNum)
            )
            
            DLInstance.Download()
            
            self.CurrentNum +=1
            
            sleep(PlaylistTimeout)
        pass


class YoutubeDL:
    def __init__(
self,
SongID      : str,
Path        : str = './Music/[Artist]/[Album]/[SongNum] - [SongName]',
APIinstance : YTMusic = YTMusic(),
APIData     : dict | None = None,
YTData      : YouTube | None = None,
AlbumName   : str | None = None,
AlbumCover  : str | None = None,
AlbumYear   : str | None = None,
AlbumArtist : str | None = None,
SongNum     : str = '0'
):
        self.SongID = SongID
        self.Path = Path
        
        self.type = YoutubeDL
        
        if APIData != None:
            self.IsSubprocess = True
            self.SongData = APIData
            self.Youtube = YTData if YTData != None else YouTube("https://youtube.com/watch?v="+self.SongID)

        else:
            self.IsSubprocess = False
            self.API = APIinstance
            self.SongData = self.API.get_song(self.SongID)['videoDetails']
            self.Youtube = YouTube('https://youtube.com/watch?v='+self.SongID)

        #self.AlbumYear = AlbumYear if AlbumYear != None else self.SongData['year']
        self.Artist = self.SongData['author']
        self.AlbumArtist = AlbumArtist if AlbumArtist != None else self.SongData['author']
        self.SongName = self.SongData['title']
        self.SongNum = SongNum
        self.AlbumCoverURL = None
        
        c = 0
        if self.SongData != None:
            for i in self.SongData['thumbnail']['thumbnails']:
                if i['width'] > c:
                    self.AlbumCoverURL = i['url']
                    c = i['width']
        
        self.AlbumCover = AlbumCover if AlbumCover != None else get(self.AlbumCoverURL).content
        self.AlbumName = AlbumName if AlbumName != None else self.SongName


    def Download(self):
        
        Path = InsertPathData(Path=self.Path,
                       Artist=self.AlbumArtist,
                       Album=self.AlbumName,
                       SongName=self.SongName,
                       SongNum=self.SongNum)
        
        SongName = Path.split('/')[-1]
        SongPath = Path.replace('/'+SongName,'')
        
        if SongName == SongPath.split('/')[-1]:
            SongName+='_'
        
        success = False
        try:
            self.Youtube.streams.get_audio_only().download(
                output_path=SongPath,
                filename=SongName
            )
            success = True
        except:
            print("Age Restriction, Trying All Clients")
            for i in _default_clients:
                try:
                    print("Trying:",i)
                    y = YouTube(self.Youtube.watch_url,i)
                    
                    y.streams.get_audio_only().download(
                        output_path=SongPath,
                        filename=SongName
                    )
                    print("Yep")
                    success = True
                except:
                    print("Nope")
        
        if not success:
            error = BaseException
            error.add_note("Age Restriction Bypass/Download No Worky")
            raise error
        
        file = AudioSegment.from_file(f"{SongPath}/{SongName}.m4a","m4a")
        file.export(f"{SongPath}/{SongName}.mp3", format="mp3")
        os.remove(f"{SongPath}/{SongName}.m4a")
        
        audiofile = eyed3.load(f"{SongPath}/{SongName}.mp3")
        audiofile.initTag()
        
        if self.Artist : audiofile.tag.artist = self.Artist
        if self.AlbumArtist : audiofile.tag.album_artist = self.AlbumArtist
        if self.AlbumName : audiofile.tag.album = self.AlbumName
        if self.SongName : audiofile.tag.title = self.SongName
        if self.SongNum : audiofile.tag.track_num = self.SongNum
        #if self.AlbumYear : audiofile.tag.release_date = self.AlbumYear

        
        if self.AlbumCover == None: pass
        else:
            FRONT_COVER = eyed3.id3.frames.ImageFrame.FRONT_COVER
            audiofile.tag.images.set(FRONT_COVER, img_data=self.AlbumCover, mime_type="image/jpg", description="Front Cover", img_url=self.AlbumCoverURL)
        
        audiofile.tag.save(encoding='utf-8', version=eyed3.id3.ID3_V2_3)



#Extras
def InsertPathData(
    Path     : str,
    Artist   : str,
    Album    : str,
    SongName : str,
    SongNum  : str
):
    
    SongNum = SongNum if len(SongNum) > 1 else '0'+SongNum
    
    Path = Path.replace('[Artist]',Artist)
    Path = Path.replace('[Album]',Album)
    Path = Path.replace('[SongName]',SongName)
    Path = Path.replace('[SongNum]',SongNum)
    
    return Path