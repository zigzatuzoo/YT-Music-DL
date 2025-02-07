from sys import argv

input = argv[1]

print(input)

albums = []
artists = []

for i in input.split(','):
    if '/playlist' in i:
        i = i.split('list=')[1].split('&si=')[0]
        albums.append(i)
    elif '/channel/' in i:
        i = i.split('/channel/')[1].split('?si=')[0]
        artists.append(i)

import MusicDL

path = '/mnt/Music/Opus-Music/[Artist]/[Album]/[SongNum] - [SongName]'
path = './TestMusic/[Artist]/[Album]/[SongNum] - [SongName]'

for a in artists:
    MusicDL.ArtistDL(path,a).Download(extra=f"Currently on artist {artists.index(a)+1}/{len(artists)}")

for a in albums:
    MusicDL.AlbumDL(path,a).Download(extra=f"Currently on album {albums.index(a)+1}/{len(albums)}")
