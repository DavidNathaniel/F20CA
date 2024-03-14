import openai
from dotenv import load_dotenv
import ast
import os
from Manager import DialogueManager as DM
import time

load_dotenv("Retico_GPT/k.env")
openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=openai_api_key)

class RestaurantManager(DM):
    def __init__(self):
        super().__init__()
        self.restaurant_slots = {
            "Location": None,
            "Timeframe": None,
            "PartySize": None,
            "Cuisine": None
        }
    
    #empty the slots
    def empty_slots(self):
        self.restaurant_slots = {
            "Location": None,
            "Timeframe": None,
            "PartySize": None,
            "Cuisine": None
        }

    def check_empty_slots(self):
        start_time = time.time()
        NoneList = []
        for slot in self.restaurant_slots.keys():
            if self.restaurant_slots[slot] in [None, 'None', 'hhmm']:
                NoneList.append(slot)
        end_time = time.time()
        time_difference = end_time - start_time
        print(f"check_empty_slots took {time_difference} seconds")
        return NoneList

    #Ask gpt to get the slots from the user input
    @staticmethod
    def sendSlotPrompt(user_response):
        start_time = time.time()
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            #put in our dictionary so gpt doesn't forget stuff?
            messages=[
                {"role": "user", "content": """{"Location": None,"Timeframe": None,"PartySize": None,"Cuisine": None}"""+f"You are a dialogue manager, please find the relevant slot and potentially other slots from this user response: '{user_response}' this response might not be semantically correct. FORMATTED PYTHON DICT ONLY.Use hhmm time."}
            ]
        )
        completion_time = time.time()
        response = completion.choices[0].message.content
        response_time = time.time()
        print(f"sendSlotPrompt completion took {completion_time - start_time} seconds")
        print(f"sendSlotPrompt response took {response_time - completion_time} seconds")
        return response

    #Ask gpt to generate a clarification question for a slot
    @staticmethod
    def sendClarification(slot):
        start_time = time.time()
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": f"You are a conversational assistant. The user needs to fill slots for a restaurant booking, could you ask for clarification about the {slot}? be apologetic about not hearing what they said. be brief in your response."}
            ]
        )
        completion_time = time.time()
        response = completion.choices[0].message.content
        response_time = time.time()
        print(f"sendClarification completion took {completion_time - start_time} seconds")
        print(f"sendClarification response took {response_time - completion_time} seconds")
        return response

    #this function is to ask the user for the slot initially if it was not given in the utterance
    @staticmethod
    def askForSlot(slot):
        start_time = time.time()
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": """slots={
        "Location": None,
        "Timeframe": None,
        "PartySize": None,
        "Cuisine": None,
        "Restaurant_type": None,
        "Restaurant_name": None,
        "Facilities": None
    }"""+f"ask a question to find the {slot}. Be brief. QUESTION ONLY"}
            ]
        )
        completion_time = time.time()
        response = completion.choices[0].message.content
        response_time = time.time()
        print(f"askForSlot completion took {completion_time - start_time} seconds")
        print(f"askForSlot response took {response_time - completion_time} seconds")
        return response

    @staticmethod
    def convert_stringtodict(input_string):
        dict = ast.literal_eval(input_string)
        return dict
     
    def updateSlots(self, gpt_slots):
        #this needs to update the restaurant_slots with the correct values for the keys
        #not sure how to extract the keys and values from the gpt output("slots") since it returns a string
        start_time = time.time()
        for key in self.restaurant_slots:
            if key not in gpt_slots.keys():
                continue
            elif gpt_slots[key] is not None:
                self.restaurant_slots[key] = gpt_slots[key]
        end_time = time.time()
        print(f"updateSlots took {end_time - start_time} seconds")
        

'''
restaurant_slots = {
    "Location": None,
    "Timeframe": None,
    "PartySize": None,
    "Cuisine": None,
    "Restaurant_type": None,
    "Restaurant_name": None,
    "Facilities": None  
}


#res = sendClarification("partySize")
#print(res)
res = sendSlotPrompt("Location", "I would like to book a restaurant in Edinburgh for 7pm")
#print(res)
gpt_slots = convert_stringtodict(res)
print("gpt slots\n",gpt_slots)
restaurant_slots = updateSlots(gpt_slots, restaurant_slots)
print("Restaurant slots after update")
print(restaurant_slots)
#print(res)
#print(list(res))


#Main loop 
for slot in restaurant_slots.keys():
    if slot is None:
        #if the's still no slot after the response, send a clarification request
        #change user_input to be the input from asr
        slots = sendSlotPrompt(slot, user_input)
        updateSlots(slots, restaurant_slots)
        if slot is None:
            resp = askForSlot(slot)
        

        while slot is None:
            res = sendClarification(slot)
            print(res)
    #make sure we do not ask for slots that have already been filled
    else:
        break
    
'''