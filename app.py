# author:nerako, David, Nedas, Gregor
# For the main screen and UI, run this function directly.
# -----------------------2024.03.14-------------------------

import eel
import record_wav
import microphone_ASR
import multiprocessing as mp
import keyboard
import pyttsx3
#import TTS_Module as tm
#import threading
import wav_ASR
#import TTS
from restaurant_manager import RestaurantManager
import time
import openai
from dotenv import load_dotenv
import TTS_Module as tts_mod
from ctypes import c_bool, c_wchar_p

if __name__ == "__main__":
    # eel.init('web') ???
    mp.set_start_method('spawn')
    load_dotenv("Retico_GPT/k.env")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=openai_api_key)
    rm = RestaurantManager()
    global user_speaking_event
    user_speaking_event = mp.Event()
    global mic_input 
    mic_input = mp.Value(c_wchar_p, lock=True)
    user_speaking_event.clear()
    mic_input.acquire()
    mic_input.value = ""
    mic_input.release()
    print("Speaking flag ", user_speaking_event.is_set())
    print("Mic input ", mic_input.value)


def identify_task(user_input):
    #function for identifying the task using GPT
    completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            #put in our dictionary so gpt doesn't forget stuff?
            messages=[
                {"role": "user", "content": f"Your job is to identify the task a user wants to carry out. The possible task are bookRestaurant, playMusic, getWeather, searchCreativeWorks,and rateBook. Find the task from this user response: '{user_input}'. RETURN TASK ONLY. If the user does not provide enough information, respond with notEnoughInfo"}
            ]
        )
    task = completion.choices[0].message.content
    return task


def clar_request(slot):
    global mic_input
    global user_speaking_event
    #send request to GPT, then update the chat text and speak the response
    ans = rm.sendClarification(slot) #
    eel.updatechattext(ans) 
    # p = multiprocessing.Process(target=speak, args=(ans,)) You have set this up twice??
    setup_speak_process(ans)

    # get the user's response, send to GPT, convert the gpt response to our python dict.
    setup_listen_process(mic_input, user_speaking_event)
    user_speaking_event.wait()
    gpt_output = rm.sendSlotPrompt(mic_input.value)
    
    print(gpt_output)
    gpt_dict = rm.convert_stringtodict(gpt_output)

    #update the slots with the new information
    rm.updateSlots(gpt_dict)
    print("Slots are: ", rm.restaurant_slots)
    print("response is: ", gpt_output)



def thread_killer(sendKillRequest=False):
    return sendKillRequest

# Function to handle microphone input
def setup_listen_process(mi, sf):
    p = mp.Process(target=listen_for_user_input, args=[mi, sf], daemon=True)
    p.start()
        
def listen_for_user_input(mic_input, user_speaking_event):
    while True:
        # Listen for microphone input
        curr_input = microphone_ASR.set_up()
        
        print("User input: ", curr_input)
        # Check if there is speech input, if so, interrupt the speaker
        if curr_input:
            # If there is speech input, set the speaking flag to True
            print("User input: ", curr_input)
            mic_input.acquire()
            try:
                mic_input.value = curr_input
            finally:
                mic_input.release()
            
            user_speaking_event.set()
            # Update the chat text with user input
            eel.updatechattext("Speaker: " + curr_input)
            break

# If user is speaking before the tts is speaking, then tts will not say anything (?)
def setup_speak_process(msg):
    p = mp.Process(target=speak, args=( msg,), daemon=True)
    p.start()
    while p.is_alive():
        if user_speaking_event.is_set(): 
            p.terminate()
        else:
            continue
    p.join()

# TTS speaker function (for multi-threading)
def speak(text):
    engine = tts_mod.create_tts_engine()
    engine.say(text)
    engine.runAndWait()

@eel.expose
def append_to_chattext():
    global mic_input
    global user_speaking_event
    start_text = "Can I help you book a restaurant? The fitness grand-pacer test is a multistage arobic test, that progressively gets more difficult as you continue."
    eel.updatechattext("ChatGPT: " + start_text)
    setup_listen_process(mic_input, user_speaking_event)
    setup_speak_process(start_text)
    start_app()
    ans = "Convo Finished" # all slots have been found, terminate conversation.
    eel.updatechattext(ans)
    print("Convo Finished")

def start_app():
    global mic_input
    global user_speaking_event
    user_speaking_event.wait()
    #Send uterance to GPT, convert the response to our python dict, and update
    mic_input.acquire()
    try:
        gpt_output = rm.sendSlotPrompt(mic_input.value)
    finally:
        mic_input.release()
        
    gpt_dict = rm.convert_stringtodict(gpt_output)
    rm.updateSlots(gpt_dict)

    print("Slots beginning: ", rm.restaurant_slots)
    keys = rm.check_empty_slots()
    print("first empty Keys are: ", keys)
    
    # loop through all keys with a None value, and request each.
    # after a key has a value, it will be removed from the list of keys.
    while keys:
        currKey = keys[0]
        print('currKey: ', currKey)

        if rm.restaurant_slots[currKey] is None: #double check...
            #GPT requests slot from user
            slot_request =  rm.askForSlot(currKey)
            eel.updatechattext("ChatGPT: "+slot_request)
            setup_listen_process(mic_input, user_speaking_event)
            setup_speak_process(slot_request)
        
            # print(f"ASR took {end_mic_time - start_mic_time} seconds")
            # print(f"Chat text took {end_chattext_time - end_mic_time} seconds")
            # print(f"Speaker took {end_chattext_time - start_speaker_time} seconds")

            mic_input.acquire()
            gpt_output = rm.sendSlotPrompt(mic_input.value)
            mic_input.release()
            print(f'GPT Response:\n{gpt_output}\n')

            # Sometimes GPT produces a dict / JSON that doesn't fit with our expected format.
            # In this instance a ValueError is raised, 
            # so we try to get a new response from GPT with the same prompt
            # Sending a clarification request is another potential fix here, depends on requirements
            try:
                gpt_dict = rm.convert_stringtodict(gpt_output)
            except ValueError: 
                print("ValueError found... retrying...")
                mic_input.acquire()
                gpt_output = rm.sendSlotPrompt(mic_input.value)
                mic_input.release()
                print(f'New GPT Response after ValueError:\n{gpt_output}\n')
                gpt_dict = rm.convert_stringtodict(gpt_output) #retry...
                print("Slots after error: ", rm.restaurant_slots)
                #clar_request(currKey)
                
        # update any slots found, and update the keys iterable
        rm.updateSlots(gpt_dict) 
        keys = rm.check_empty_slots()
        print("Slots updated: ", rm.restaurant_slots)
        print("Keys are: ", keys)

        # if the slot is still empty, request clarification from GPT
        while currKey in keys:
            clar_request(currKey)
            print("Slots after looped clarification request: ", rm.restaurant_slots)
            keys = rm.check_empty_slots()
            print("Keys in loop are: ", keys)
    return 
   
    # p = multiprocessing.Process(target=speak, args=(ans,))
    #global flag_tts
    # flag_tts = False
    # setup_speak_process(p)
    
    #this resets the conversation once it is finished. 
    #Alternative is to rest when user presses speak button
    # rm.empty_slots()# = RestaurantManager()
    
    #just in case
    # m.join()
        #

    # @eel.expose
    # def update_speaktext(ans):
    #     eel.updatespeaktext(ans)

    # @eel.expose
    # def start_app():
    #     eel.start('index.html', size=(1100, 950))

if __name__ == "__main__":
    eel.start('index.html', size=(1100, 950))
