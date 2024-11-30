import json
import selenium
from selenium import webdriver
#import selenium.webdriver as webdriver
from youtube_transcript_api import YouTubeTranscriptApi
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import os
import isodate
import requests
from urllib.parse import urlparse, parse_qs

load_dotenv()




from selenium.webdriver.common.by import By
path ="/Users/markattar/Downloads/Code/Chrome/chromedriver-mac-arm64"
#driver = webdriver.Chrome()
YOUTUBE_API_KEY=os.getenv("YOUTUBE_API_KEY")
CLIENT_SECRET= os.getenv("CLIENT_SECRET")
CLIENT_ID = os.getenv("CLIENT_ID")
def pretty_print_transcript(transcript):
    for item in transcript:
        print(item)
        print("\n\n\n")
        # print(f"Time: {item['start']} - {item['end']}")
        # print(f"Speaker: {item['speaker']}")
        # print(f"Text: {item['text']}")
        # print("------------------------")

#Really what I need is to take the audio/video of both and create matching transcripts using the same audio to text tool, resulting in matching transcripts

def store_transcript(transcript, filename):
    with open(filename, 'w') as f:
        json.dump(transcript, f, indent=4)


def getGameTranscript(fname, game):

    with open(fname) as jsonF:
        data = json.load(jsonF)
        transcript = data[game]['transcript']
        store_transcript(transcript, f"{game} transcript.txt")
        return transcript



def getTeams(fname, keys):
    teamDict = {}
    with open(fname) as jsonF:
        data = json.load(jsonF)
        for key in keys:
            elem = data[key]
            teams = elem['teams']
            teamDict[elem] = teams
        
    return teamDict
        


#Function takes the json file and returns the video queries and keys of the different matches 
def pullJSON(fname):

    with open(fname) as jsonF:
        
        #jsonloads
        #what do i do first...

        i = 0 
        data = json.load(jsonF)
        
        keys = data.keys()
        key_list = list(keys)
        store_transcript(key_list, 'key_list.txt')
        #print(data['2018-tennessee_titans-tampa_bay_buccaneers.txt'])

        e = jsonF.readline()
        transcriptStructure = {}

        sorted_keys = sorted(key_list, key= lambda x: int(x.split('-')[0]))

        sorted_video_queries = []

        for key in sorted_keys:
            transcript, teams = data[key]['transcript'], data[key]['teams']
            
            transcriptStructure[key] = {'transcript': transcript, 'teams': teams}
            #cut off txt
            stringTake = key[:-4]
            strList = stringTake.split('-')
            if strList[-1].isdigit():
                continue
            team1 = " ".join(strList[1].split('_'))
            team2 = " ".join(strList[2].split('_'))
            query = strList[0] + ' ' +team1 +' versus ' + team2 + ' highlights'
            sorted_video_queries.append(query)

        return sorted_keys, sorted_video_queries, transcriptStructure
    
    #Extracting video id from client is an interesting concept 


#Okay new concept: 1. Search queries, 2. Search for video URL w/Perplexity API, 3. Use AssemblyAI API/Whisper API to transcribe the highlights 

#Don't need it: Video id is in the url we don't have to transcribe 



#Perplexity API is a good choice if this doesn't work 
#https://youtube.googleapis.com/youtube/v3/captions?part=snippet&videoId=tx2Ws1n7BMc&key=
   
#Search API req
#https://youtube.googleapis.com/youtube/v3/search?part=snippet&q=2018 Tennessee Titans vs Tampa Bay Buccaneers>&type=video&maxResults=5&key=






def minutesToSeconds(minutes):
    return minutes * 60

def getUrl(message):

    perplexityURL = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "find best possible football highlight youtube videos"
            },
            {
                "role": "user",
                "content": f"{message}"
            }
        ],
        "max_tokens": "Optional",
        "temperature": 0.2,
        "top_p": 0.9,
        "search_domain_filter": ["perplexity.ai"],
        "return_images": False,
        "return_related_questions": False,
        "search_recency_filter": "month",
        "top_k": 0,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 1
    }
    headers = {
        "Authorization": "Bearer <token>",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    print(response.text)

def getYoutubeTranscript(search_query:str, nfl:bool, minute_limit = 20):
    
    # search = driver.find_element(By.ID,"search")
    # search.send_keys(search_query)

    try:
        res = requests.get(f"https://youtube.googleapis.com/youtube/v3/search?part=snippet&q={search_query}&type=video&maxResults=5&key={YOUTUBE_API_KEY}")
        data = res.json()
        
        if 'error' in data:
            print("Error received in request", data['error'])
            return None
        
        items = data['items']
        chosenID = ""
        #details request 
        i = 0 
        #How to pick the best between the top 5 video results I think its more like we need to know whether these are highlights/too long
        for item in items:
            videoID = item['id']['videoId']
            contentRes = requests.get(f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={videoID}&key={YOUTUBE_API_KEY}") 
            contentData = contentRes.json()
            snippet, contentDetails = item['snippet'], contentData['items'][0]['contentDetails']
            isoDur = isodate.parse_duration(contentDetails['duration'])
            duration = isoDur.total_seconds()
            if duration > minutesToSeconds(minute_limit):
                continue    
            channelName = snippet['channelTitle']
            title = snippet['title']
            
            #checking for highlights & nfl, but I think I need a more robust solution that can semantically pick from the top 5 (if this doesn't work, perplexity api)
            if nfl and channelName == 'NFL':  
                chosenID = videoID
                break
            if 'highlights' in title.lower():
                chosenID = videoID
                break
            
            i += 1
        if chosenID == "":
            return None
        try:
            transcript = YouTubeTranscriptApi.get_transcript(chosenID, languages=['en'])
        except Exception as e:
            return None
        
        #pretty_print_transcript(transcript)
        return transcript
        #store_transcript(transcript, f"YOUTUBE {search_query} transcript.txt")

    except HttpError as e:
        print("Error: " + str(e))

    #auth URL: https://accounts.google.com/o/oauth2/auth
    #Access token URL: https://oauth2.googleapis.com/token
    #Scope: https://www.googleapis.com/auth/youtube.force-ssl
    #Send as Basic Auth header


    

def addLabelsToTranscript(transcript, highlights):
    pass
    


    
#channelTitle


def main():

    #NO ONE ELSE CAN SPEAK THE WORDS FOR YOU


    nfl_teams = {
    "arizona_cardinals",
    "atlanta_falcons",
    "baltimore_ravens",
    "buffalo_bills",
    "carolina_panthers",
    "chicago_bears",
    "cincinnati_bengals",
    "cleveland_browns",
    "dallas_cowboys",
    "denver_broncos",
    "detroit_lions",
    "green_bay_packers",
    "houston_texans",
    "indianapolis_colts",
    "jacksonville_jaguars",
    "kansas_city_chiefs",
    "las_vegas_raiders",
    "los_angeles_chargers",
    "los_angeles_rams",
    "miami_dolphins",
    "minnesota_vikings",
    "new_england_patriots",
    "new_orleans_saints",
    "new_york_giants",
    "new_york_jets",
    "philadelphia_eagles",
    "pittsburgh_steelers",
    "san_francisco_49ers",
    "seattle_seahawks",
    "tampa_bay_buccaneers",
    "tennessee_titans",
    "washington_commanders"
    }
    fname = 'raw_transcripts.json'
    game = '2018-tennessee_titans-tampa_bay_buccaneers.txt'

    #checkJSON(fname)
    #printGameTranscript(fname, game)

    #print(webdriver)
    #driver.get("https://www.youtube.com/")


    #Structure will be key: {
    #  transcript:
    #  highlights: ,
    #  modified: ,


    #}

    sorted_keys, video_queries, transcriptStructure = pullJSON(fname)
    print(sorted_keys)

    n = len(video_queries)
    
    # for i in range(n):
    #     key, query = sorted_keys[i], video_queries[i]
    #     print(query)
    #     if transcriptStructure[key]['teams'][0] in nfl_teams:
    #         nfl = True
    #     else:
    #         nfl = False
    #     #get the original transcript, need all original transcripts + the highlights + the
    #     highlights = getYoutubeTranscript(query, nfl)
        
    #     transcriptStructure[key]['highlights'] = highlights
        
    getGameTranscript(fname, "2016-kentucky-tennessee-1.txt")

    getGameTranscript(fname, "2016-kentucky-tennessee.txt")


    # t = getYoutubeTranscript("2018 Tennessee Titans vs Tampa Bay Buccaneers", True)
    # store_transcript(t, "YOUTUBE 2018 Tennessee Titans vs Tampa Bay Buccaneers transcript.txt")

    


#we had the transcripts but we needed to get the full versions & compile the data 
#so I guess training is just showing this text without the labels
#NO the training is compiling a list of token labels that go with the tokens & labeling them in/out of highlight

#Step 1 is to fix up the pipeline so it gets all of the compiled transcripts along with their appropriate highlight videos 
#

#Read papers on span


# "2016-kentucky-tennessee-1.txt",
  #  "2016-kentucky-tennessee.txt",


if __name__ == "__main__":
    main()


#Current problems

#1. Mismatch between highlight (subtitles) and original transcript
#2. Ran out of youtube data api need more
#3. Need to get this trained 
#4. Seemingly multiple games for same team/same year
#5. 



