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
import TTS_Module as tts_mod
from ctypes import c_bool, c_wchar_p

if __name__ == "__main__":
    eel.init('web')
    mp.set_start_method('spawn')
    
    rm = RestaurantManager()
    global user_speaking_event
    user_speaking_event = mp.Event()
    global main_con, mic_con
    main_con, mic_con = mp.Pipe()
    user_speaking_event.clear()
    global engine
    engine = tts_mod.create_tts_engine()

    # print("Speaking flag ", user_speaking_event.is_set())



# initiate a clarification request from GPT for the relevant slot.
def clar_request(slot):
    global engine
    global mic_con
    global main_con
    global user_speaking_event
    #send request to GPT, then update the chat text and speak the response
    ans = rm.sendClarification(slot) #
    eel.updatechattext(ans) 
    # p = multiprocessing.Process(target=speak, args=(ans,)) You have set this up twice??
    setup_listen_process(mic_con, user_speaking_event)
    # setup_speak_process(ans)
    engine.say(ans)
    engine.runAndWait()
    # user_speaking_event.wait()
    curr_Utt = main_con.recv()
    user_speaking_event.clear()
    # get the user's response, send to GPT, convert the gpt response to our python dict.
    gpt_output = rm.sendSlotPrompt(curr_Utt)
    
    print("GPT's response is: ", gpt_output)
    gpt_dict = rm.convert_stringtodict(gpt_output)

    print("Current slots are: ", rm.restaurant_slots)

    #update the slots with the new information
    rm.updateSlots(gpt_dict)
    print("Updated slots are: ", rm.restaurant_slots)


# Function to handle microphone input
def setup_listen_process(con_to_main, user_speaking_event):
    p = mp.Process(target=listen_for_user_input, args=(con_to_main, user_speaking_event), daemon=True)
    p.start()
        
def listen_for_user_input(con_to_main, user_speaking_event):
    while True:
        # Listen for microphone input
        curr_input = microphone_ASR.set_up()
        
        print("User input: ", curr_input)
        # Check if there is speech input, if so, interrupt the speaker
        if curr_input:
            # If there is speech input, set the speaking flag to True
            print("User input: ", curr_input)
            
            con_to_main.send(curr_input)
            user_speaking_event.set()
            # Update the chat text with user input
            print("User speaking event is set: aaaa", user_speaking_event.is_set())
            break

# If user is speaking before the tts is speaking, then tts will not say anything (?)d
def interrupt_speaker(name, location, length):
    global main_con
    print ('word', name, location, length)
    print("User speaking event is set: ", user_speaking_event.is_set())
    print("Main con is: ", main_con.poll())
    if main_con.poll():
        print("User is speaking, please wait.")
        engine.stop()
        # engine.say("User is speaking, please wait.")
        # engine.runAndWait()
        # print("2User is speaking, please wait2.")

def setup_speak_process(msg):
    global engine
    # p = mp.Process(target=speak, args=( msg,), daemon=True)
    engine.connect('started-word', interrupt_speaker)
    engine.say(msg,"msg")
    engine.runAndWait()
    # p.start()
    # print(p.name)
    # while p.is_alive():
    #     if user_speaking_event.is_set(): 
    #         print("User is speaking, terminating: " + p.name)
    #         p.terminate()
    #     else:
    #         continue
    # p.join()

# TTS speaker function (for multi-threading)
def speak(text, engine):
    # engine = tts_mod.create_tts_engine()
    engine.say(text)
    engine.runAndWait()

@eel.expose
def append_to_chattext():
    global user_speaking_event
    global main_con
    global mic_con
    start_text = "Can I help you book a restaurant? The fitness grand-pacer test is a multistage arobic test, that progressively gets more difficult as you continue."
    eel.updatechattext("ChatGPT: " + start_text)
    setup_listen_process(mic_con, user_speaking_event)
    setup_speak_process(start_text)
    find_info()
    ans = "Convo Finished" # all slots have been found, terminate conversation.
    eel.updatechattext(ans)
    print("Convo Finished")
    return

def find_info():
    global engine
    global main_con
    global mic_con
    global user_speaking_event
    print("starting wait")
    curr_Utt = main_con.recv()
    eel.updatechattext("Speaker: " + curr_Utt)
    user_speaking_event.clear()
    #Send uterance to GPT, convert the response to our python dict, and update
    gpt_output = rm.sendSlotPrompt(curr_Utt)
        
    
    try:
        gpt_dict = rm.convert_stringtodict(gpt_output)
    except ValueError: 
        print("ValueError found... retrying...")
        gpt_output = rm.sendSlotPrompt(curr_Utt)
        print(f'New GPT Response after ValueError:\n{gpt_output}\n')
        gpt_dict = rm.convert_stringtodict(gpt_output) #retry...
        print("Slots after error: ", rm.restaurant_slots)
        #clar_request(currKey)    rm.updateSlots(gpt_dict)

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
            setup_listen_process(mic_con, user_speaking_event)
            # setup_speak_process(slot_request)
            engine.say(slot_request)
            engine.runAndWait()
            curr_Utt = main_con.recv()
            user_speaking_event.clear()
        

            gpt_output = rm.sendSlotPrompt(curr_Utt)
            print(f'GPT Response:\n{gpt_output}\n')

            # Sometimes GPT produces a dict / JSON that doesn't fit with our expected format.
            # In this instance a ValueError is raised, 
            # so we try to get a new response from GPT with the same prompt
            # Sending a clarification request is another potential fix here, depends on requirements
            try:
                gpt_dict = rm.convert_stringtodict(gpt_output)
            except ValueError: 
                print("ValueError found... retrying...")
                gpt_output = rm.sendSlotPrompt(curr_Utt)
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
