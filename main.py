import os 
import time 
from instagrapi import Client 
from instagrapi.exceptions import LoginRequired
import logging
import json
from instagrapi import exceptions
import subprocess
from PIL import Image, ImageEnhance
import hashlib
import random
from datetime import datetime
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import requests
from instagrapi.exceptions import (
    BadPassword, ReloginAttemptExceeded, ChallengeRequired,
    SelectContactPointRecoveryForm, RecaptchaChallengeForm,
    FeedbackRequired, PleaseWaitFewMinutes, LoginRequired
)

random_captions = [
    "When life gives you lemons, make memes 🍋😂 #Selfsup #MemeLife",
    "If laughter is the best medicine, consider this your daily dose 🤣💊 #Selfsup",
    "Tag someone who needs a laugh today 😂👇 #Selfsup #DailyMeme",
    "Current mood: meme overload 🤯😂 #Selfsup #MemeAddict",
    "When you realize it's only Tuesday... 😅 #Selfsup #MidweekStruggles",
    "If you can't relate, you're lying 😂 #Selfsup #TruthBomb",
    "Trying to adult, but my inner child has other plans 🤪 #Selfsup #AdultingFail",
    "Laughing through the pain, one meme at a time 🤣 #Selfsup #ComedyRelief",
    "When the Wi-Fi is slow, but your meme game is strong 💪😂 #Selfsup #InternetStruggles",
    "The face you make when you see your crush 😂😍 #Selfsup #CrushCringe",
    "Who needs therapy when you have memes? 😂 #Selfsup #MemeTherapy",
    "When the squad is as crazy as you are 🤪 #Selfsup #SquadGoals",
    "Reality called, I hung up 😂📞 #Selfsup #RealityCheck",
    "That moment when your meme gets more likes than your selfie 😂 #Selfsup #MemeGoals",
    "Mood: Just here for the memes 🤷‍♀️ #Selfsup #MemeMood",
    "If only life had a meme filter 😂 #Selfsup #LifeGoals",
    "When your playlist is on point, but so is your meme game 🎶😂 #Selfsup #PlaylistVsMemes",
    "Sometimes all you need is a good laugh and a great meme 😂 #Selfsup #LaughOutLoud",
    "When you realize you're not the only one who struggles with mornings 😂☕ #Selfsup #MorningStruggles",
    "If you don't laugh at this, we can't be friends 😂 #Selfsup #FriendTest"
]

def handle_exception(client, e):
    if isinstance(e, BadPassword):
        client.logger.exception(e)
        client.set_proxy(self.next_proxy().href)
        if client.relogin_attempt > 0:
            self.freeze(str(e), days=7)
            raise ReloginAttemptExceeded(e)
        client.settings = self.rebuild_client_settings()
        return self.update_client_settings(client.get_settings())
    elif isinstance(e, LoginRequired):
        client.logger.exception(e)
        client.relogin()
        return self.update_client_settings(client.get_settings())
    elif isinstance(e, ChallengeRequired):
        api_path = json_value(client.last_json, "challenge", "api_path")
        if api_path == "/challenge/":
            client.set_proxy(self.next_proxy().href)
            client.settings = self.rebuild_client_settings()
        else:
            try:
                client.challenge_resolve(client.last_json)
            except ChallengeRequired as e:
                self.freeze('Manual Challenge Required', days=2)
                raise e
            except (ChallengeRequired, SelectContactPointRecoveryForm, RecaptchaChallengeForm) as e:
                self.freeze(str(e), days=4)
                raise e
            self.update_client_settings(client.get_settings())
        return True
    elif isinstance(e, FeedbackRequired):
        message = client.last_json["feedback_message"]
        if "This action was blocked. Please try again later" in message:
            self.freeze(message, hours=12)
            # client.settings = self.rebuild_client_settings()
            # return self.update_client_settings(client.get_settings())
        elif "We restrict certain activity to protect our community" in message:
            # 6 hours is not enough
            self.freeze(message, hours=12)
        elif "Your account has been temporarily blocked" in message:
            """
            Based on previous use of this feature, your account has been temporarily
            blocked from taking this action.
            This block will expire on 2020-03-27.
            """
            self.freeze(message)
    elif isinstance(e, PleaseWaitFewMinutes):
        self.freeze(str(e), hours=1)
    raise e

def retry_operation(operation, *args, **kwargs):
    retries = 3
    for attempt in range(retries):
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error during operation: {e}")
            if attempt < retries - 1:
                logger.info(f"Retrying... ({attempt + 1}/{retries})")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Failed operation after {retries} attempts")
                raise e

# sets up function for logging in 
logger = logging.getLogger(__name__)

def login_user(username, password):
    """
    Attempts to login to Instagram using either the provided session information
    or the provided username and password.
    """

    client = Client()
    client.handle_exception = handle_exception
    session = client.load_settings("session.json")
    
    login_via_session = False
    login_via_password = False

    if session:
        try: 
            client.set_settings(session)
            client.login(username, password)
        
            # check if session is valid 
            try:
                client.get_timeline_feed()
            except LoginRequired:
                logger.info("Session is invalid, need to login with username and password") 

                old_session = client.get_settings()

                # use the same devide uuids across logins 
                client.set_settings({})
                client.set_uuids(old_session['uuids'])

                client.login(username, password)
            login_via_session = True
        except Exception as e:
            logger.info("Couldn't login user using session information %s" % e)

    if not login_via_session:
        try:
            logger.info("Attempting to login using username and password. username: %s" % username)
            if client.login(username, password):
                login_via_password = True
        except Exception as e:
            logger.info("Couldn't login user using username and password: %s" % e) 

    if not login_via_session and not login_via_password:
        raise Exception("Couldn't login user using either session or username and password")

    return client
  
# create function to save media photos and videos 
def save_media(client, username, latest_post): 
    """
    Saves the media from the specified user to the current directory.
    """

    if latest_post.media_type == 1: # photo
        client.photo_download(latest_post.pk, folder='tmpdown')
        print(f"Saved {latest_post.user.username}_{latest_post.taken_at}_{latest_post.id}.jpg")
        print("Processing image...")
        process_image(f"tmpdown/{latest_post.user.username}_{latest_post.pk}.jpg", f"processed_content/{latest_post.user.username}_{latest_post.id}.jpg")
        if latest_post.caption_text: 
            caption = generate_caption(latest_post.caption_text)
        else:
            caption = f"{random.choice(random_captions)} \n from @{latest_post.user.username}"
        client.photo_upload(f"processed_content/{latest_post.user.username}_{latest_post.id}.jpg", caption)

    elif latest_post.media_type == 2 and latest_post.product_type == "feed": # video
        retry_operation(client.video_download, latest_post.pk, folder='tmpdown')
        print(f"Saved {latest_post.user.username}_{latest_post.pk}.mp4")
        print("Processing video...")
        process_video(f"tmpdown/{latest_post.user.username}_{latest_post.pk}.mp4", f"processed_content/{latest_post.user.username}_{latest_post.id}.mp4")
        if latest_post.caption_text: 
            caption = generate_caption(latest_post.caption_text)
        else:
            caption = f"{random.choice(random_captions)} \n from @{latest_post.user.username}"
        client.video_upload(f"processed_content/{latest_post.user.username}_{latest_post.id}.mp4", caption)

    elif latest_post.media_type == 8: # carousel - NEEDS TO BE CHECKED IDK OUTPUT 
        print("Downloading carousel images...")
        client.album_download(latest_post.pk, folder='tmpdown')
        print(f"Saved {latest_post.user.username}_{latest_post.taken_at}_{latest_post.id}.mp4")
        print("Processing image...") # PROCESSING IS NOT THERE YET 
        if latest_post.caption_text:  
            caption = generate_caption(latest_post.caption_text)
        else:
            caption = f"{random.choice(random_captions)} \n from @{latest_post.user.username}"
        client.album_upload(f"tmpdown/{latest_post.user.username}_{latest_post.pk}", caption)

    elif latest_post.media_type == 2 and latest_post.product_type == "clips": # reels
        client.clip_download(latest_post.pk, folder='tmpdown')
        print(f"Saved {latest_post.user.username}_{latest_post.taken_at}_{latest_post.id}.mp4")
        print("Processing reels...")
        process_video(f"tmpdown/{latest_post.user.username}_{latest_post.pk}.mp4", f"processed_content/{latest_post.user.username}_{latest_post.id}.mp4")
        if latest_post.caption_text:  
            caption = generate_caption(latest_post.caption_text)
        else:
            caption = f"{random.choice(random_captions)} \n from @{latest_post.user.username}"
        client.clip_upload(f"processed_content/{latest_post.user.username}_{latest_post.id}.mp4", caption)

    else:
        return None

# using pretrained model to generate captions for images
def generate_caption(caption):
    torch.random.manual_seed(0)

    model = AutoModelForCausalLM.from_pretrained(
        "microsoft/Phi-3-mini-4k-instruct", 
        device_map="cuda", 
        torch_dtype="auto", 
        trust_remote_code=True, 
    )
    tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")

    messages = [
    {"role": "system", "content": "ONLY PROVIDE THE CAPTION TEXT HERE. DO NOT INCLUDE ANY OTHER INFORMATION."},
    {"role": "user", "content": "Can you reword the following sentence as an instagram caption: 'I like to eat bananas and dragonfruits together'?"},
    {"role": "assistant", "content": "Enjoying the perfect combo of bananas and dragonfruits! 🍌🐉 #HealthyEats #FruitLove"},
    {"role": "user", "content": "Can you reword the following sentence as an instagram caption: " + caption},
]

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
    )

    generation_args = {
        "max_new_tokens": 50,
        "return_full_text": False,
        "temperature": 0.3,
        "do_sample": True,
    }

    output = pipe(messages, **generation_args)
    new_caption = (output[0]['generated_text'])
    return new_caption

# processes video to remove data
def process_video(video_path, output_path):
    try:
        # Generate a temporary output file
        temp_output = "temp_output.mp4"
        
        # Adjust contrast randomly between 7% and 12%
        contrast_factor = 1 + random.uniform(0.07, 0.12)
        
        # Construct the ffmpeg command
        command = [
            'ffmpeg', '-i', video_path,
            '-vf', f'eq=contrast={contrast_factor},format=yuv420p',
            '-metadata', 'a=0', '-c:a', 'copy', temp_output
        ]
        
        # Run the ffmpeg command and capture stderr output
        result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
        
        # Check for errors in the stderr output
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return None
        
        # Rename the temporary output file to the final output path
        os.rename(temp_output, output_path)
        
        # Update MD5 hash
        with open(output_path, 'rb') as f:
            md5_hash = hashlib.md5(f.read()).hexdigest()
        
        logger.info(f"Processed video saved to {output_path} with MD5: {md5_hash}")
        return md5_hash
    
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg CalledProcessError: {e}")
        return None
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        return None

# processes photo to remove data
def process_image(image_path, output_path):
    # Open the image
    image = Image.open(image_path)
    
    # Remove metadata by saving the image without it
    data = list(image.getdata())
    new_image = Image.new(image.mode, image.size)
    new_image.putdata(data)
    
    # Adjust contrast randomly between 7% and 12%
    contrast_factor = 1 + random.uniform(0.07, 0.12)
    enhancer = ImageEnhance.Contrast(new_image)
    new_image = enhancer.enhance(contrast_factor)
    
    # Save the image to remove any existing metadata
    new_image.save(output_path, format='JPEG', quality=95)
    
    # Update MD5 hash
    with open(output_path, 'rb') as f:
        md5_hash = hashlib.md5(f.read()).hexdigest()

# create monitor function to check for new posts from usernames 
def monitor_accounts(client, usernames): 
    """
    Monitors the specified accounts for new posts.
    """
    last_post_times = {username: None for username in usernames}

    while True:
        for username in usernames: 
            try: 
                user_id = client.user_id_from_username(username)
                posts = client.user_medias(user_id, 4)

                if posts:
                    latest_post = max(posts, key=lambda post: post.taken_at)
                    post_time = latest_post.taken_at

                    if last_post_times[username] is None or post_time > last_post_times[username]:
                        last_post_times[username] = post_time
                        print(f"New post from {username} at {post_time}")
                        save_media(client, username, latest_post)
            except exceptions.ClientError as e:
                logger.error(f"Error monitoring {username}: {e}")
            
        time.sleep(3600) # check every 15 minute
        print("Checking for new posts...")
        print("Clearning tmpdown folder...")
        



if __name__ == "__main__":

    # reads in credentials from file
    with open('credentials.txt', 'r') as f: 
        username, password = f.read().splitlines()

    try:  
        client = login_user(username, password)
        client.delay_range = [2, 16]
        logger.info("Logged in successfully")

        usernames_to_monitor = ["repostrandy"] # create a list of usernames to monitor
        monitor_accounts(client, usernames_to_monitor)

    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


