import json
import requests
import random




def getRng():
    response = requests.get("https://3icecream.com/js/songdata.js")
    if response.status_code != 200:
        return "network error...uhhh try max300 buddy???:)"#this is the rarest response hahahaaaa
    prefix = b'var ALL_SONG_DATA='
    suffix = b';const EVENT_EXCLUSIONS=[30,40,50,60,70,80,90,110,120,130,140,150,170,180,200,210,220,230,240,260,270,290,300];const SONG_DATA_LAST_UPDATED_unixms=1754722897432;'
    rng = []
    for fetched_song in json.loads(response.content[len(prefix):-len(suffix)]):  #[len(prefix):-len(suffix)]):
                title = fetched_song['song_name']
                ratings=fetched_song['ratings']
                l = fetched_song['song_id']

                if l!="006i1i6OOl1bPdql9ID8o6QQ6IIiqP0P":
                    
                    rate = []
                    #eh lets just get the difficulties we care about playing, screw doubles too
                    for i in range(2,len(ratings)-2,1):
                        rate.append(ratings[i])
                        if(ratings[i]<ratings[i-1]):
                              i = len(ratings) #end this
                                
                        
                        
                    rng.append([title, rate])
    index = random.randint(0, len(rng))
    ans = "Hmm, how about try playing " + str(rng[index][0]) + ", you can try the singles " + str(rng[index][1][0])  + " or maybe "  + str(rng[index][1][1]) + " if ya feeling quirky, gl gamer! >:)"
    return ans

