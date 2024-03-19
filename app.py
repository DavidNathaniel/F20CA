# author:nerako, David, Nedas, Gregor
# For the main screen and UI, run this function directly.
# -----------------------2024.03.14-------------------------

import eel
import record_wav
import microphone_ASR
import multiprocessing
import keyboard
import pyttsx3
#import TTS_Module as tm
#import threading
import wav_ASR
#import TTS
from restaurant_manager import RestaurantManager
import time
import TTS_Module as tts_mod

if __name__ == "__main__":
    eel.init('web')
    rm = RestaurantManager()
    #print('witchcraft here')
    #engine = tts_mod.create_tts_engine()

    global flag_tts
    flag_tts = False

engine = tts_mod.create_tts_engine()

# initiate a clarification request from GPT for the relevant slot.
def clar_request(slot):
    #send request to GPT, then update the chat text and speak the response
    ans = rm.sendClarification(slot) #
    eel.updatechattext(ans) 
    p = multiprocessing.Process(target=speak, args=(ans,))
    global flag_tts
    flag_tts = False
    setup_speak_process(p)

    # get the user's response, send to GPT, convert the gpt response to our python dict.
    start_time = time.time()
    mic_input = microphone_ASR.set_up()
    end_time = time.time()
    print(f"ASR took {end_time - start_time} seconds")
    gpt_output = rm.sendSlotPrompt(mic_input)
    print(gpt_output)
    gpt_dict = rm.convert_stringtodict(gpt_output)

    #update the slots with the new information
    rm.updateSlots(gpt_dict)
    print("Slots are: ", rm.restaurant_slots)
    print("response is: ", gpt_output)

    #def activate(text, createEngine=False):
    #engine = tts_mod.create_tts_engine()
    #speak(text)

def thread_killer(sendKillRequest=False):
    return sendKillRequest

# Function to handle microphone input
def microphone_thread():
    while True:
        # Listen for microphone input
        mic_input = microphone_ASR.set_up()
        # Check if there is speech input, if so, interrupt the speaker
        if mic_input:
            '''    # User response:
            mic_input = microphone_ASR.set_up()
            ans =  "Speaker: " + mic_input
            eel.updatechattext(ans)'''
            # Terminate the speaker process
            #p.terminate()
            # Update the chat text with user input
            eel.updatechattext("Speaker: " + mic_input)

# If user is speaking before the tts is speaking, then tts will not say anything (?)
def setup_speak_process(p):
    global flag_tts
    #p = multiprocessing.Process(target=speak, args=( msg,))
    #flag_tts = False
    p.start()
    while p.is_alive():
        #print('while activated')
        #instead: if the person speaks (not if they press'q')
        if flag_tts: #keyboard.is_pressed('q'): #mic_input:
            #kill the proces (interrupt)
            p.terminate()
            #UI. destroy should go here?
            # ...
        else:
            #listen for user input (?)
            continue
    p.join()

# TTS speaker function (for multi-threading)
def speak(text):
    engine.say(text)
    engine.runAndWait()

def mic_setup(q):
    global flag_tts
    print('flag currently is: ', flag_tts)
    mic_input = microphone_ASR.set_up()
    for word in mic_input:
        q.put(word)

    if mic_input in ['', None]:
        print('mic_input is empty')
    else:
        print('has something in here.....')
    while not mic_input:
        continue
    else:
        flag_tts = True
        print('flag set.....')
        yield mic_input

if __name__ == "__main__":
    @eel.expose
    def append_to_chattext():
        global flag_tts
        mic_input = "" #microphone_ASR.set_up()
        q = multiprocessing.Queue()
        m = multiprocessing.Process(target=mic_setup, args=(q,))
        m.start()
        #mic_input = mic_setup()
        '''for word in mic_input:
            print(f'x is {word}')'''
        while True:
            word = q.get()  # This will block until there's something in the queue
            if word is None:  # We send None to indicate that there's no more data
                break
            print(f'x is {word}')

        # engine.stop()
        
        # update chat text with GPT and user responses
        # GPT repsonse:
        msg = "Can I help you book a restaurant? The fitness grand-pacer test is a multistage arobic test, that progressively gets more difficult as you continue."
        eel.updatechattext("ChatGPT: " + msg)
        #set up new thread,
        '''p = multiprocessing.Process(target=speak, args=( msg,))
        #m = multiprocessing.Process(target=, args=( msg,))

        p.start()
        while p.is_alive():
            #print('while activated')
            #instead: if the person speaks (not if they press'q')
            if keyboard.is_pressed('q'): #mic_input:
                #kill the proces (interrupt)
                p.terminate()
                #UI. destroy should go here?
                # ...
            else:
                #listen for user input (?)
                continue
        p.join()
        '''
        
        p = multiprocessing.Process(target=speak, args=(msg,))
        #global flag_tts
        flag_tts = False
        setup_speak_process(p)

        #m = multiprocessing.Process(target=, args=( msg,))
        #gpt has overwritten the keys in the dict.
        #
        #
        # User response:
        #mic_input = microphone_ASR.set_up()
        #ans =  "Speaker: " + mic_input
        #eel.updatechattext(ans)
        
        #Send uterance to GPT, convert the response to our python dict, and update
        gpt_output = rm.sendSlotPrompt(mic_input)
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
                start_speaker_time = time.time()
                
                #tts_mod.speak(slot_request)
                #will need to set up a new process.
                p = multiprocessing.Process(target=speak, args=(slot_request,))
                #global flag_tts
                flag_tts = False
                setup_speak_process(p)
                

                #listen for user utterance, then send to GPT
                start_mic_time = time.time()
                #mic_input = microphone_ASR.set_up()
                end_mic_time = time.time()
                eel.updatechattext("Speaker: " +mic_input)
                end_chattext_time = time.time()

                print(f"ASR took {end_mic_time - start_mic_time} seconds")
                print(f"Chat text took {end_chattext_time - end_mic_time} seconds")
                print(f"Speaker took {end_chattext_time - start_speaker_time} seconds")

                gpt_output = rm.sendSlotPrompt(mic_input)
                print(f'GPT Response:\n{gpt_output}\n')

                # Sometimes GPT produces a dict / JSON that doesn't fit with our expected format.
                # In this instance a ValueError is raised, 
                # so we try to get a new response from GPT with the same prompt
                # Sending a clarification request is another potential fix here, depends on requirements
                try:
                    gpt_dict = rm.convert_stringtodict(gpt_output)
                except ValueError: 
                    print("ValueError found... retrying...")
                    gpt_output = rm.sendSlotPrompt(mic_input)
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

        ans = "Convo Finished" # all slots have been found, terminate conversation.
        eel.updatechattext(ans)
        p = multiprocessing.Process(target=speak, args=(ans,))
        #global flag_tts
        flag_tts = False
        setup_speak_process(p)
        
        #this resets the conversation once it is finished. 
        #Alternative is to rest when user presses speak button
        rm.empty_slots()# = RestaurantManager()
        
        #just in case
        m.join()
        #

    # @eel.expose
    # def update_speaktext(ans):
    #     eel.updatespeaktext(ans)

    # @eel.expose
    # def start_app():
    #     eel.start('index.html', size=(1100, 950))
    if __name__ == "__main__":
        eel.start('index.html', size=(1100, 950))