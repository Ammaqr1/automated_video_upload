import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv
import re
import asyncio
import edge_tts
from moviepy.editor import *
from bing_image_downloader import downloader
import os
import random
import moviepy.config as cfg
import shutil
from PIL import Image
import time
from upload_video2 import upload_video


# from tts import extract_keywords,scrape_images

from downloads import path_download
from bg_music import current_path



load_dotenv()


# class Character(BaseModel):
#     name: str
#     fact: list[str] = Field(..., description="A list of facts about the subject")



class Model:
    def __init__(self,prompt):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.conversation = [{'role':'user','content':prompt}]
        self.srp_img = []
        self.all = []
        
    def model(self,prompt = '',model='gemma2-9b-it',cln_txt = '',system_prompt = ''):
        if cln_txt:
            self.srp_img.append({'role':'system','content':system_prompt})
            self.srp_img.append({'role':'user','content':prompt + cln_txt})
            self.all = self.srp_img
        else:
            
            self.all = self.conversation
            
        chat_completion = self.client.chat.completions.create(
        messages=self.all
        ,
        model= model,
        temperature=0.3
         )

        output = chat_completion.choices[0].message.content
        
        self.conversation.append({'role':'assistant','content':output})
        self.all = []
        
        return output
    
    def time_stamp_preprocessing(self,text):
        pattern = r'\[(\d+:\d+ - \d+:\d+)\](.*?)(?=\[|$)'

        matches = re.findall(pattern, text, re.DOTALL)

        cleaned_sentences = [f"[{timestamp}] {sentence.strip()}" for timestamp, sentence in matches]

        return cleaned_sentences
    
    def remove_time_stamp(self,cleaned_sentences):
        cleaned_text = ''
        for i in cleaned_sentences:
            cleaned_text += i[15:]
        cleaned_text =  cleaned_text.encode('utf-8').decode('unicode_escape')
        return cleaned_text
    
    
    async def tts(self,cleaned_text):
        voice = 'en-US-AriaNeural'
        text = cleaned_text
        output_file = 'audio.mp3'
        
        communicate = edge_tts.Communicate(text, voice,rate='+18%')
        await communicate.save(output_file)
        
    def keyword_sorting(self,text):
        keywords_list = [line.strip() for line in text.split('\n') if line.strip()]
        if len(keywords_list) > 6:
            keywords_list.pop(0)
        return keywords_list
    
    
    def adjust_audio_length(self,audio_clip, target_duration):
        if audio_clip.duration < target_duration:
            # Loop the audio to extend its duration
            audio_clip = audio_clip.fx(vfx.loop, duration=target_duration)
        return audio_clip.subclip(0, target_duration)
    

    def create_video_from_images(self,image_folder, audio_path, output_path, bg_music_path):
        transition_duration = 0.5
        duration_per_image = 1.7

        # Step 1: Load images from the folder
        images = sorted(
            [
                os.path.join(root, img)
                for root, dirs, files in os.walk(image_folder)
                for img in files
                if img.endswith(("png", "jpg", "jpeg"))
            ]
        )

        if not images:
            print(f"No images found in {image_folder}. Please check the folder path and content.")
            return

        valid_images = []
        for img_path in images:
            try:
                with Image.open(img_path) as img:
                    print(f"Successfully opened: {img_path}")
                    rgb_img = img.convert("RGB")
                    resized_img = rgb_img.resize((1920, 1080))  # Adjust to desired size
                    resized_img.save(img_path)
                    valid_images.append(img_path)
            except Exception as e:
                print(f"Error processing {img_path}: {e}")

        images = valid_images
        if not images:
            print("No valid images were found after processing.")
            return

        # Step 2: Create a list of clips with transitions
        clips = []
        for img_path in images:
            try:
                image_clip = ImageClip(img_path).set_duration(duration_per_image).resize((1080, 1920))
                clips.append(image_clip)

                # Add a transition clip (fade to black)
                transition = ColorClip(size=image_clip.size, color=(0, 0, 0), duration=transition_duration).fadein(transition_duration)
                clips.append(transition)
            except Exception as e:
                print(f"Error creating clip for {img_path}: {e}")

        if not clips:
            print("No clips were created. Please check the images and transitions.")
            return

        # Concatenate the clips
        video = concatenate_videoclips(clips, method="compose")

        # Step 3: Add background audio
        audio = AudioFileClip(audio_path)
        bg_music = AudioFileClip(bg_music_path)
        bg_music = self.adjust_audio_length(bg_music, audio.duration)

        # Mix audio with background music
        mixed_audio = CompositeAudioClip([audio, bg_music.volumex(0.3)])
        video = video.set_audio(mixed_audio)

        # Step 4: Trim video to match audio duration
        if video.duration > audio.duration:
            video = video.subclip(0, audio.duration)

        # Step 5: Write the final video to the output path
        try:
            video.write_videofile(output_path, fps=24, codec="libx264")
        except Exception as e:
            print(f"Error writing video: {e}") 
            print('please ignore this error')          
                
            
    def scrape_images(self,query, limit=2):
        downloader.download(query, limit=limit, output_dir=path_download.path_for_image_downloder_cwd(), adult_filter_off=True, force_replace=False, timeout=60)
    
    def clean_folder_name(self,folder_name):
        
        name = re.sub(r'^\d+\.\s*', '', folder_name)
        
        invalid_chars = r'<>:"/\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name   
    
    def delete_folders_in_directory(self, directory_path=path_download.path_for_image_downloder_cwd()):
        try:
            # Check if the given path is valid
            if not os.path.isdir(directory_path):
                print(f"Error: {directory_path} is not a valid directory.")
                return
            
            # List all items in the directory
            items = os.listdir(directory_path)
            
            # Iterate through items and delete folders
            for item in items:
                item_path = os.path.join(directory_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"Deleted folder: {item_path}")
                else:
                    print(f"Skipped non-folder item: {item_path}")
            
            print("All folders inside the specified directory have been deleted successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")
            
            
    
    def audio_length(self,audio_path):
        audio = AudioFileClip(audio_path)
        return audio.duration
    
    
    
    def calculate_images_from_audio(self,audio_duration, transition_duration = 0.5, duration_per_image=1.7):

        # Calculate total time per image (including transition)
        time_per_image = duration_per_image + transition_duration
        
        # Calculate the number of images needed
        num_images = audio_duration / time_per_image
        
        return int(num_images/6) 
    
    def bg_music_selector(self,path):
        count = 0
        bg_music_list = []
        for i,music_path in enumerate(os.listdir(path)):
            if music_path.endswith('mp3'):
                bg_music_list.append(music_path)
                count += 1
            
        return ''.join(bg_music_list[random.randint(0,count-1)])
    
                       
    
prompt = """

"Create an engaging 45-second European football story with a powerful curiosity-driven hook.

Hook examples:
- "Have you ever heard of a goalkeeper scoring in a Champions League final?"
- "Did you know there was once a match where both teams refused to score?"
- "What if I told you the greatest comeback in football history happened in just 6 minutes?"

Choose one focus:
- Hidden gems from Champions League/European Cup history
- Unbelievable match moments that changed football
- Lesser-known records that sound impossible
- Mind-blowing coincidences in major tournaments

Story structure:
[00:00 - 00:08] Curiosity hook + immediate intrigue
[00:08 - 00:15] Key players/setting
[00:15 - 00:25] Build anticipation
[00:25 - 00:35] Lead to climax
[00:35 - 00:40] The revelation
[00:40 - 00:45] Brief, impactful conclusion

Writing guidelines:
- Start with a question or "What if" statement
- Use specific details but keep descriptions tight
- Build tension through pacing
- End with a satisfying payoff

Keep total length under 120 words for natural delivery."
"""

model = Model(prompt)



scrape_prompt = '''
"Generate 6 distinct image search phrases based on the provided football story.

Requirements for each phrase:
1. Length: 10-15 words each
2. Must include:
   - Team names and relevant kits/colors
   - Specific action or emotion being captured
   - Match context (tournament/competition name)
   - Location/stadium if mentioned

Format each phrase for optimal image search:
- Focus on key moments from the story
- Progress chronologically through the narrative
- Include both action and reaction shots
- Mix wide shots and close-ups
- Ensure phrases will return real football images
- Avoid overly specific details that might limit results

Note: Phrases should be general enough to find real football images while matching the story's atmosphere and emotion."

'''

system_prompt = '''
"You are a football historian specializing in creating authentic image search phrases that match the exact era of 
each story."

'''


while True:

    story = model.model()
    print(story)

    model.delete_folders_in_directory()
    
    
    
    asyncio.run(model.tts(cleaned_text=story))
    time.sleep(5)
    audio_l = model.audio_length()    
    limit = model.calculate_images_from_audio(audio_l)
    print(limit)




    output = model.model(scrape_prompt,cln_txt=story,model='mixtral-8x7b-32768',system_prompt=system_prompt)
    print(output)
    keys = model.keyword_sorting(output)
    for i,phrase in enumerate(keys):
        print(phrase)
        val = model.clean_folder_name(phrase)
        model.scrape_images(query=val,limit=limit + 1)


    image_folder = path_download.path_for_image_downloder_cwd()
    audio_path = "audio.mp3"  
    output_path = "output_video.mp4"  
    music_path = model.bg_music_selector(current_path.cwdd())
    bg_music_path = os.path.join(current_path.cwdd(), music_path)



    model.create_video_from_images(image_folder,audio_path,output_path=output_path,bg_music_path=bg_music_path)
    
    # time.sleep(10*5)
    
    video_data = {
            "file": r'C:\Users\ammar\Documents\from_scratch\output_video.mp4',
            "title": "Interesting Football Story!",
            "description": "#shorts \n Sharing the best football story for 2025",
            "keywords":"meme,reddit,footballstory",
            "privacyStatus":"public"
        }
    upload_video(video_data)
    
    
    print('successfully uploaded')
    print('time to sleep ')
    
    time.sleep(5 * 100)


    print('deleted folder successfully')
    



        
                    