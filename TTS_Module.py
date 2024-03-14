# author:nerako
# This program is used to synthesize speech
# -----------------------2024.2.16-------------------------

import pyttsx3
import multiprocessing
import keyboard



def __init__():
    engine = pyttsx3.init()
    # base set
    rate = engine.getProperty('rate')
    engine.setProperty('rate', 150)

    volume = engine.getProperty('volume')
    engine.setProperty('volume', 1.0)

    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)
    print("TTS engine is ready!")
    return engine

def speak(engine, text):
    a = engine.say(text)
    engine.runAndWait()
    engine.stop()

def sayFunc(engine, phrase):
    #engine = pyttsx3.init()
    #self.engine.setProperty('rate', 160)
    engine.say(phrase)
    engine.runAndWait()

def say_words(engine, phrase):
    #if __name__ == "__main__":
    print('did it work?')
    p = multiprocessing.Process(target=sayFunc, args=(phrase,))
    p.start()
    while p.is_alive():
        print('while activated')
        if keyboard.is_pressed('q'):
            p.terminate()
        else:
            continue
    p.join()
    #self.engine.stop()

#def save(self):
#    self.engine.save_to_file('words', filename='filename', name='name')
#    self.engine.runAndWait()

# if __name__ == '__main__':
#     NEW_TTS = TTS()
#     NEW_TTS.speak("Conversational Agents and Spoken Language Processing")