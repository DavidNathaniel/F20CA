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
import create_correct_class_for_task as ccc
import time
import os
import openai
from dotenv import load_dotenv
import TTS_Module as tts_mod
from ctypes import c_bool, c_wchar_p

if __name__ == "__main__":
    eel.init('web')
    mp.set_start_method('spawn')
    load_dotenv("Retico_GPT/k.env")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=openai_api_key)
    global main_con, mic_con
    main_con, mic_con = mp.Pipe()

def identify_task(user_input):
    #function for identifying the task using GPT
    completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": f"Your job is to identify the task a user wants to carry out. The possible task are bookRestaurant, playMusic, getWeather, searchCreativeWorks,and rateBook. Find the task from this user response: '{user_input}'. RETURN TASK ONLY. If the user does not provide enough information, respond with notEnoughInfo"}
            ]
        )
    task = completion.choices[0].message.content
    return task

def clar_request(manager, slot):
    global mic_con
    global main_con
    #send request to GPT, then update the chat text and speak the response
    ans = manager.sendClarification(slot) #
    eel.updatechattext(ans) 
    setup_listen_process(mic_con)
    setup_speak_process(ans)

    curr_Utt = main_con.recv()
    # get the user's response, send to GPT, convert the gpt response to our python dict.
    gpt_output = manager.sendSlotPrompt(curr_Utt)
    
    print("GPT's response is: ", gpt_output)
    
    gpt_dict = manager.convert_stringtodict(gpt_output)

    print("Current slots are: ", manager.slots)

    #update the slots with the new information
    manager.updateSlots(gpt_dict)
    print("Updated slots are: ", manager.slots)


# Function to handle microphone input
def setup_listen_process(con_to_main):
    p = mp.Process(target=listen_for_user_input, args=(con_to_main, ), daemon=True)
    p.start()
        
def listen_for_user_input(con_to_main):
    while True:
        # Listen for microphone input
        curr_input = microphone_ASR.set_up()
        
        print("User input: ", curr_input)
        # Check if there is speech input, if so, interrupt the speaker
        if curr_input:
            # If there is speech input, set the speaking flag to True
            print("User input: ", curr_input)
            
            con_to_main.send(curr_input)
            # Update the chat text with user input
            break

def setup_speak_process(msg):
    global main_con
    p = mp.Process(target=speak, args=( msg,), daemon=True)
    p.start()
    print(p.name)
    while p.is_alive():
        if main_con.poll(): 
            print("User is speaking, terminating: " + p.name)
            p.terminate()
        else:
            continue

# TTS speaker function (for multi-threading)
def speak(text):
    engine = tts_mod.create_tts_engine()
    engine.say(text)
    print("Speaking: ", text)
    engine.runAndWait()

@eel.expose
def append_to_chattext():
    global main_con
    global mic_con
    start_text = "hello how can I help you today? I am currently able to help you by searching for a craetive work or booking a restaurant. Please feel free to interrupt me at any time."
    eel.updatechattext("ChatGPT: " + start_text)
    setup_listen_process(mic_con)
    setup_speak_process(start_text)
    find_info()
    ans = "Convo Finished" # all slots have been found, terminate conversation.
    eel.updatechattext(ans)
    print("Convo Finished")
    return

def find_info():
    global main_con
    global mic_con
    print("starting wait")
    curr_Utt = main_con.recv()
    eel.updatechattext("Speaker: " + curr_Utt)
    #print("Identified task: " + identify_task(curr_Utt))
    manager = ccc.create_class(identify_task(curr_Utt))
    while manager is None:
        clar = "I'm sorry I am currently only able to help you by searching for a creative work or booking a restaurant. Please try again."
        eel.updatechattext("ChatGPT:" + clar)
        setup_listen_process(mic_con)
        setup_speak_process(clar)
        curr_Utt = main_con.recv()
        manager = ccc.create_class(identify_task(curr_Utt))
        #print(identify_task(curr_Utt))
    #Send uterance to GPT, convert the response to our python dict, and update
    gpt_output = manager.sendSlotPrompt(curr_Utt)
    print(f'GPT Response:\n{gpt_output}\n')
    
    gpt_dict = manager.convert_stringtodict(gpt_output)

    print("Slots beginning: ", manager.slots)
    keys = manager.check_empty_slots()
    print("first empty Keys are: ", keys)
    
    # loop through all keys with a None value, and request each.
    # after a key has a value, it will be removed from the list of keys.
    while keys:
        currKey = keys[0]
        print('currKey: ', currKey)

        if manager.slots[currKey] is None: #double check...
            #GPT requests slot from user
            slot_request =  manager.askForSlot(currKey)
            eel.updatechattext("ChatGPT: "+slot_request)
            setup_listen_process(mic_con)
            setup_speak_process(slot_request)
            curr_Utt = main_con.recv()

            gpt_output = manager.sendSlotPrompt(curr_Utt)
            print(f'GPT Response:\n{gpt_output}\n')

            # Sometimes GPT produces a dict / JSON that doesn't fit with our expected format.
            # In this instance a ValueError is raised, 
            # so we try to get a new response from GPT with the same prompt
            # Sending a clarification request is another potential fix here, depends on requirements
            gpt_dict = manager.convert_stringtodict(gpt_output)

        # update any slots found, and update the keys iterable
        manager.updateSlots(gpt_dict) 
        keys = manager.check_empty_slots()
        print("Slots updated: ", manager.slots)
        print("Keys are: ", keys)

        # if the slot is still empty, request clarification from GPT
        while currKey in keys:
            clar_request(manager, currKey)
            print("Slots after looped clarification request: ", manager.slots)
            keys = manager.check_empty_slots()
            print("Keys in loop are: ", keys)
    return 

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
