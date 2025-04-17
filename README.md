CutUp NLP Sports Highlights Project 

Automatically detect and extract the most exciting moments from full-game commentary transcripts, aligning them with highlight videos using state-of-the-art NLP.

Why This Project

Watching every second of a sports broadcast can be time-consuming. What if you could skip straight to the game’s best plays? NLP Highlights Project uses natural language processing to:

Identify key commentary snippets (e.g. goals, touchdowns).

Align them with official highlight videos.

Generate precise timestamped segments for quick playback.

Whether you’re a coach reviewing performances, a fan catching up on highlights, or a data scientist exploring NLP in sports, this tool has you covered.

Features

Full-Game Transcript Ingestion: Pulls commentary from YouTube using the YouTube API & Selenium.

Highlight Detection: Leverages transformer models (GPT‑2 & BERT) to classify commentary segments.

Timestamp Alignment: Maps detected highlights to exact video timestamps.

Export Formats: CSV, JSON, or direct video clip extraction scripts.

Modular & Extensible: Swap in new models or integrate with other video platforms.

Pipeline Overview

The NLP Highlights pipeline consists of seven core stages, each implemented as a modular function in run_pipeline.py:

Transcript Extraction• fetch_subtitles(video_url) — retrieves captions via the YouTube Data API or falls back to Selenium scraping.• Normalizes timestamps and merges multi-language tracks.

Preprocessing• clean_transcript(text) — removes filler tokens, corrects encoding issues, and filters out non-commentary lines.

Segmentation• segment_transcript(clean_text, window_s) — splits the transcript into fixed-length windows (e.g., 5 s) with overlap for context.

Feature Extraction• compute_embeddings(chunks) — uses a transformer embedding model (BERT) to represent each text chunk in vector space.

Highlight Classification• rank_highlights(embeddings) — applies a pretrained GPT‑2 classifier head to score each chunk’s “highlight probability.”• Selects top‑K segments above a threshold.

Timestamp Mapping• map_to_video_timestamps(chunks, subtitle_metadata) — converts chunk indices back to video timecodes based on caption offsets.

Output Generation & Clip Extraction• export_results(format) — writes highlights.csv or highlights.json with {start_time,end_time,text}.• extract_clips(csv_file) — (optional) invokes ffmpeg to produce individual MP4 highlight clips.

The pipeline is orchestrated sequentially in run_pipeline.py but designed so each function can be invoked independently for testing or extension.

Tech Stack

Component

Technology

Programming Language

Python 3.8+

Web Scraping

Selenium, YouTube Data API

Data Processing

Pandas, NumPy

NLP Models

Hugging Face Transformers (GPT‑2, BERT)

Video Handling

ffmpeg (via Python subprocess)

Quick Start

Clone the repo

git clone https://github.com/markattarcolgate64/nlphighlightsproject.git
cd nlphighlightsproject

Create & activate a virtual environment

python3 -m venv venv
source venv/bin/activate

View results

highlights.csv with timestamps and play descriptions.

highlights.json for programmatic consumption.

How It Works

Transcript Extraction: Scrapes or fetches subtitles for the full game.

Segmentation: Splits transcript into fixed-length chunks.

Highlight Classification: Runs each chunk through GPT‑2/BERT to score highlight probability.

Timestamp Mapping: Converts text indices into video timestamps using subtitle metadata.

Export & Clip: Writes structured outputs and (optional) extracts video clips via ffmpeg.



This project is MIT‑licensed.

Built by Mark Attar – feel free to open issues or reach out via GitHub.

Paper
[Mark_Attar_24Fall_NLP_Final_Paper.pdf](https://github.com/user-attachments/files/19790216/Mark_Attar_24Fall_NLP_Final_Paper.pdf)
