#1. Use Selenium to do searches
#2. Use OpenAI API to select best video out of top 5 
#3. Get the transcript or audio from url we'll try transcript first 
#3. Use Whisper API to transcribe (bc I think my bank acct is linked)
#4. Tokenize transcripts & highlights (probably just split on space) & create the label arrays 
#5. Create train/test/val splits (80/10/10)
#6. Use Google cloud to train (biggest GPU)
#7. Then I need to evaluate too, which will be hard

from data_processing import pullJSON, getGameTranscript, store_transcript
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv
import openai
import json
import random
from rapidfuzz import process, fuzz
import os, time

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#potential blacklist feature if length over 

#Function uses Selenium to pull the video resources from youtube
def get_youtube_results(n, query):
    # Configure Selenium for headless operation
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Initialize the WebDriver
    driver = webdriver.Chrome(options=options)

    try:
        # Search YouTube with the query
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        driver.get(search_url)
        time.sleep(3)  # Wait for the page to load
    
        # Locate the video elements


        video_elements = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.XPATH, '//ytd-video-renderer'))  # Replace with the actual locator
)
        video_elements = video_elements[:n]

        # Extract information
        results = []
        for video in video_elements:
            try:

                
                # Extracting data from video elements
                title_element = video.find_element(By.XPATH, './/a[@id="video-title"]')
                title = title_element.text
                url = title_element.get_attribute('href')
                

                channel_elem = video.find_element(By.ID, 'channel-name')
                container = channel_elem.find_element(By.ID, 'text')
                # channel_a_tag = WebDriverWait(driver,10).until(
                #     EC.visibility_of_element_located((By.XPATH, './/a'))
                # )
                channel_a_tag= container.find_element(By.TAG_NAME, 'a')
                channel_name = channel_a_tag.get_attribute('textContent')


                # duration_element = video.find_element(By.XPATH, './/ytd-thumbnail-overlay-time-status-renderer/span')
                # duration = duration_element.text.strip()

                # Append result
                results.append({
                    'title': title,
                    'url': url,
                    'channel_name': channel_name,
                })
            except Exception as e:
                # Handle potential exceptions gracefully
                print(f"Error extracting information from a video: {e}")

        return results

    finally:
        # Close the browser
        driver.quit()

'''


'''

#FN uses OpenAI API to select best video from list 
def select_best_video(video_choices:list):
    videoMssg = ""

    for i in range(len(video_choices)):
        videoMssg += f'{i}: {video_choices[i]}\n'


    systemPrompt = 'You are a selector of football youtube highlights videos and can only respond with numerical numbers like 1,2,3...etc'
    footballMessage = f"Select the best football highlights youtube video from the following list, only return the number\n {videoMssg}"


    # Define the conversation
    messages = [
        {"role": "system", "content": systemPrompt},
        {"role": "user", "content": footballMessage}
    ]
    model = 'gpt-3.5-turbo'
    # Make the API call
    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=100,
        temperature=0.3
    )

    # Extract and return the model's reply
    print(response)
    choice = response.choices[0].message.content
    try: 
        best =  int(choice)
        return best
    except ValueError:
        return choice


#Okay so if this is complete dogwater use Whisper instead
def getHighlightTranscript(url):
    parsed_url = urlparse(url)
    query_params =  parse_qs(parsed_url.query)
    videoId = query_params['v'][0]

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id=videoId)
    except Exception as e:
        return None
    return transcript

def fuzzyMatch(query, bigString, start):

    qLen= len(query)
    bestScore = 0
    startIndex = start
    for i in range(start, len(bigString) - qLen):
        segment_string = bigString[i:i+qLen]
        score = fuzz.ratio(query, segment_string)
        if score > bestScore:
            bestScore = score 
            startIndex = i
        
    return startIndex, qLen

        


def labelTranscript(original_transcript:str, highlight_transcript:list):
    original_transcript = original_transcript.lower()
    tokens = original_transcript.split()
    labels = ['o'] * len(tokens)
    currHighlight = ""
    lastLocation = 0 
    for elem in highlight_transcript:
        text = elem['text'].lower()
        #exclude applause for now, in future we will include it with multimodal data
        #okay lets go
        word_list = text.split()
        
        if len(word_list) == 1:
            if word_list[0].strip() != '[Applause]':
                currHighlight += text
            continue 
        
        if currHighlight:
            currHighlight += text
            start, qLen = fuzzyMatch(currHighlight, tokens, lastLocation)
            currHighlight = ""
        else:
            start, qLen = fuzzyMatch(word_list, tokens, lastLocation)
        lastLocation = start + qLen
        #search for position in transcript
        for j in range(start, start + qLen):
            labels[j] = 'H'

    return labels 

    #tokens, labels
            

def pullHighlightTranscripts(keys, queries, transcriptStructure) :

    for i in range(len(queries)):
        #get youtube first
        query, key = queries[i], keys[i]
        videos = get_youtube_results(1, query)
        best_video = select_best_video(videos)
        if type(best_video) == str:
            continue
        selected_video = videos[best_video-1]
        highlights = getHighlightTranscript(selected_video['url'])
        transcriptStructure[key]['highlights'] = highlights
    return transcriptStructure
    
#now we have highlights, OG transcripts, we just need to compare and add the labels 


def putItTogether(sorted_keys, video_queries, ):
    pass

def splitData(dataset:dict):

    train_size = int(len(dataset) * 0.8)
    test_size = int(len(dataset) * 0.1)
    val_size = len(dataset) - train_size - test_size

    # Get the keys of the dictionary
    keys = list(dataset.keys())

    # Shuffle the keys
    random.shuffle(keys)

    # Split the keys into training, testing, and validation sets
    train_keys = keys[:train_size]
    test_keys = keys[train_size:train_size+test_size]
    val_keys = keys[train_size+test_size:]

    # Create the training, testing, and validation dictionaries
    datasets = {}
    datasets['train'] = {key: dataset[key] for key in train_keys}
    datasets['test']  = {key: dataset[key] for key in test_keys}
    datasets['val']  = {key: dataset[key] for key in val_keys}

    return datasets


def main():
    fname = 'raw_transcripts.json'
    sorted_keys, video_queries, transcriptStructure = pullJSON(fname)
    #we have to drop the repeat games & Nones
    sorted_keys, video_queries, transcriptStructure = ['2016-memphis-south_florida.txt'], ['2016 memphis vs south florida football game highlights'], {'2016-memphis-south_florida.txt': {'transcript': getGameTranscript(fname, '2016-memphis-south_florida.txt'), 'teams': ['memphis', 'south florida']}}
    transcriptStructure = pullHighlightTranscripts(sorted_keys, video_queries, transcriptStructure)
    formatDataset = {}
    w = labelTranscript(transcriptStructure["2016-memphis-south_florida.txt"]['transcript'], transcriptStructure["2016-memphis-south_florida.txt"]['highlights'])
    
    transcriptStructure["2016-memphis-south_florida.txt"]['labels'] = w
    store_transcript(transcriptStructure, 'transcriptStructure.json')

    #print(w)
    # for t in transcriptStructure:
    #     game = transcriptStructure[t]
    #     transcriptStructure[t]['labels'] = labelTranscript(game['transcript', game['highlights']])
    #     formatDataset[t] = {'tokens': game['transcript'], 'labels': game['labels']}
    # Split the data into training, testing, and validation sets
    
    datasets = splitData(formatDataset)
    for d in datasets:
        datasets[d] = json.dumps(datasets[d])

    print(datasets)
    datasets = {}
    # search_query = "2016 ohio state versus wisconsin football game highlights"
    # num_results = 5
    # results = get_youtube_results(num_results, search_query)
    # # for idx, result in enumerate(results):
    # #     print(f"{idx + 1}. {result}")


# Example usage
if __name__ == "__main__":
    main()    


#Then we move this to azure and start running the full pipeline in the cloud,
#Resolve issues, probably have to install a number of packages
#Then we train & evaluate using the hugging face code 