import yt_dlp
import music_tag
from ytmusicapi import YTMusic
from os import system
from requests import get
import subprocess




def DLSong(url, location):
    with yt_dlp.YoutubeDL({'extract_audio': True, 'format': '251', 'outtmpl': f'{location}.webm'}) as video:
        video.download(url)


def insertpathdata(
    Path: str,
    Artist : str,
    Album : str,
    SongNum : int,
    SongName : str):
    
    Path = Path.replace('[Artist]', Artist)
    Path = Path.replace('[Album]', Album)
    Path = Path.replace('[SongNum]', str(SongNum))
    Path = Path.replace('[SongName]', SongName)
    return Path


def convert_webm_to_opus(input_file, output_file):
    command = [
        "ffmpeg",
        "-i", f'{input_file}',
        "-vn",  # Discard video stream
        "-c:a", "libopus",  # Use the Opus codec
        "-b:a", "128k",  # Set bitrate (adjust as needed)
        #'-hide_banner',
        '-loglevel','error',
        output_file
    ]
    subprocess.run(command)




class AlbumDL:
    def __init__(self,
                 Path: str = '~/Music/[Artist]/[Album]/[SongNum] - [SongName]',
                 AlbumID : str | None = None,
                 BrowseID : str | None = None,
                 API : YTMusic | None = None,
                 AAOverride : str | None = None):
        self.api = API if API != None else YTMusic()
        
        self.Path = Path
        self.AlbumID = AlbumID
        self.BrowseID = self.api.get_album_browse_id(self.AlbumID) if BrowseID == None else BrowseID
        
        self.data = self.api.get_album(self.BrowseID)
        
        self.AlbumName = self.data['title']
        self.AlbumArtist = self.data['artists'][0]['name'] if AAOverride == None else AAOverride
        self.ReleaseYear = self.data['year']
        
        
        aurl = None
        x = 0
        for i in self.data['thumbnails']:
            if i['width'] > x:
                aurl = i['url']
                x = i['width']
        
        self.AlbumCoverURL = aurl
        self.AlbumCover = get(self.AlbumCoverURL).content
        
        
    
    def Download(self):
        print(f'Downloading the album {self.AlbumName} by {self.AlbumArtist}')
        
        Songs : list = self.data['tracks']
        
        for Song in Songs:
            try:
                WatchID = Song['videoId']
                url = 'https://music.youtube.com/watch?v='+WatchID
                
                Artists = self.AlbumArtist
                for i in Song['artists']:
                    if i['name'] != self.AlbumArtist:
                        Artists+='; '+i['name']
                
                SongName = Song['title']
                SongNum = Songs.index(Song)+1
                #Lyrics = self.api.get_lyrics(self.api.get_watch_playlist(WatchID)['tracks'][0]['lyrics'],False)
                
                Path = insertpathdata(self.Path,
                                    self.AlbumArtist,
                                    self.AlbumName,
                                    SongNum,
                                    SongName)
                
                print(f'Downloading {SongName} {SongNum}/{len(Songs)}')
                
                DLSong(url,Path)
                
                print('Converting with ffmpeg ...')
                convert_webm_to_opus(Path+'.webm',Path+'.opus')
                system(f'rm "{Path}.webm"')
                
                print('Tagging ...')
                musicfile = music_tag.load_file(Path+'.opus')
                
                musicfile['artwork'] = self.AlbumCover
                musicfile['album'] = self.AlbumName
                musicfile['albumartist'] = self.AlbumArtist
                musicfile['artist'] = Artists
                musicfile['tracktitle'] = SongName
                musicfile['tracknumber'] = SongNum
                musicfile['totaltracks'] = len(Songs)
                musicfile['year'] = self.ReleaseYear
                #musicfile['lyrics'] = Lyrics
                
                musicfile.save()
                print('Done')
                pass
            except Exception as e:
                print(f"Error downloading song: {e}\n Continuing ...")
        
        pass




class ArtistDL:
    def __init__(self,
                 Path : str = '~/Music/[Artist]/[Album]/[SongNum] - [SongName]',
                 ChannelID : str = "UCwZEU0wAwIyZb4x5G_KJp2w",
                 API : YTMusic | None = None
                 ):
        self.Path = Path
        self.api = API if API != None else YTMusic()
        
        self.ChannelID = ChannelID
        
        self.data = self.api.get_artist(self.ChannelID)
        
        self.ArtistName = self.data['name']
        
        self.Albums = []
        
        if 'albums' in self.data.keys():
            for i in self.data['albums']['results']:
                self.Albums.append(i)
        if 'singles' in self.data.keys():
            for i in self.data['singles']['results']:
                self.Albums.append(i)
        
        
        pass
    
    
    def Download(self):
        print(f'Downloading the discography of {self.ArtistName}')
        
        for album in self.Albums:
            print(f"Starting on the album {self.Albums.index(album)+1}/{len(self.Albums)} - {album['title']}")
            
            DL = AlbumDL(
                self.Path,
                BrowseID=album['browseId'],
                AAOverride=self.ArtistName)
            
            DL.Download()
