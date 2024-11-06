# nlphighlightsproject
NLP project to classify highlights from sports matches and then generate timestamps of those highlights for new videos.

Plan of execution:
1. Pull transcripts  from FOOTBALL dataset OR if this is not enough data I will go online and scrape publicly available full transcripts from soccer games from sites like ESPN, BBC and ONEFOOTBALL
2. I would line up timestamps within the matches to the commentary line by line
3. Then I would use the Youtube API to scrape the transcripts of the highlights of these complete matches, which may require some manual cleaning (all highlights of pretty much any sports match is available on Youtube)
4. The idea would be to focus on a single outlet like ESPN, pull the full commentary along with the commentary from the highlights which should match. Additionally, if I cannot get transcripts I can use AssemblyAI to transcribe the audio.
5. Preprocess data so that text is divided by timestamp along with a label for highlight
6. Use the highlight transcripts to label data in longer transcripts
7. Take the train split of the labeled data and train the models (GPT2 & BERT) on the labeled transcripts 
Evaluate the model on an unlabeled test split of the longer transcripts while using the labels to measure success
8. If time is remaining, do some software engineering to pull the timestamps of the labeled highlights so that videos can be segmented programmatically. 
