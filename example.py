import MusicDL


artists = [
    #Tally Hall
    'UC9xRJvhCNHF3Kv8j9jEA6tQ',
    #Kudasai Beats
    'UCumJMf6sc_oiLpIElQWUiOQ',
    #Yot Club
    'UCRtYGtOFiQ3g76xTYNEKf7Q',
    #Joji
    'UCXi-Rme73-wjVK5IE78a3SQ',
    #D4vd
    'UCGr1UQ4CwzRMmYoQfHQQWTg',
    #Chezile
    'UCxPmk7reHHCAAiN4lmth4OA',
    #Nujabes
    'UCxQQET-tQsC4cwzLow9ZsuQ',
    #Voj
    'UCxpQCKU1rh3sGIJuIpkMsNA',
    
    ]

path = '/mnt/Music/Opus-Music/[Artist]/[Album]/[SongNum] - [SongName]'

for a in artists:
    MusicDL.ArtistDL(a,path).Download()



albums = [
    #Witnessing the birth of light - Black Hill
    'OLAK5uy_lkY3f5oaptWkV3hfcF1xaM9jBhMIgAm58',
    #Minecraft - Volume Alpha - C418
    'OLAK5uy_nafOyxSwDvUta0pkBIkQfpUV6qKZ1jQaw',

    ]

for a in albums:
    MusicDL.AlbumDL(path,a)