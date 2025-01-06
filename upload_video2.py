import os
import time
import random
from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
import httplib2

import streamlit as st

from dotenv import load_dotenv
from authenticate import get_authenticated_service  # Import from authentication.py

load_dotenv()

# Define retry parameters
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

def initialize_upload(youtube, video_data):
    body = {
        'snippet': {
            'title': video_data['title'],
            'description': video_data['description'],
            'tags': video_data['keywords'].split(",") if video_data['keywords'] else None,
            # 'categoryId': video_data['category'],
        },
        'status': {
            'privacyStatus': video_data['privacyStatus']
        }
    }

    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(video_data['file'], chunksize=-1, resumable=True)
    )

    resumable_upload(insert_request)

def resumable_upload(insert_request):
    response = None
    retry = 0
    error = None  # Initialize error here
    while response is None:
        try:
            print("Uploading file...")
            status, response = insert_request.next_chunk()
            if response is not None:
                if 'id' in response:
                    print("Video id '%s' was successfully uploaded." % response['id'])
                else:
                    exit("The upload failed with an unexpected response: %s" % response)
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = "A retriable error occurred: %s" % e

        if error is not None:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                exit("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print("Sleeping %f seconds and then retrying..." % sleep_seconds)
            time.sleep(sleep_seconds)

def upload_video(video_data):
    youtube = get_authenticated_service()
    try:
        initialize_upload(youtube, video_data)
    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred:\n{e.content}")

if __name__ == '__main__':
    video_data = {
        "file": r'C:\Users\ammar\Documents\from_scratch\output\output_video.mp4',
        "title": "Interesting Football Story!",
        "description": "#shorts \n Sharing the best football story for 2025",
        "keywords": "meme,reddit,footballstory",
        "privacyStatus": "private"
    }
    upload_video(video_data)