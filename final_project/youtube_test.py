# https://github.com/alexmercerind/youtube-search-python
#Sync
# pip3 install youtube-search-python

from youtubesearchpython import VideosSearch
import json
videosSearch = VideosSearch('나루토', limit = 10)
json_res = videosSearch.result()
# print(videosSearch.result())  ## [{},{},{}]

print(json.dumps(videosSearch.result(), sort_keys=True, indent=4))

movie_list = json_res['result']
for movie in movie_list:
    print(movie['thumbnails'][0]['url'])
    print(movie['link'])
