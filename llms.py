from langchain_google_genai import ChatGoogleGenerativeAI

import json

import os

llms = {

    "llm_1": ChatGoogleGenerativeAI(

        model="gemini-1.5-flash",

        temperature=0,

        max_tokens=None,

        timeout=None,

        max_retries=3,

        api_key="AIzaSyCj02FWwvOF5zEYoA3n6JjhF2NZrBiVBjY"

    ),

    "llm_2": ChatGoogleGenerativeAI(

        model="gemini-1.5-flash",

        temperature=0,

        max_tokens=None,

        timeout=None,

        max_retries=3,

        api_key="AIzaSyAwn9E1avvE4DRy5JTAMmY0lFmJCACUbLI"
    ),

    "llm_3": ChatGoogleGenerativeAI(

        model="gemini-1.5-flash",

        temperature=0,

        max_tokens=None,

        timeout=None,

        max_retries=3,

        api_key="AIzaSyBJUnHcBp5yApOpRMyYQexF9sOEblgSmnI"
        
    ),
    
     "llm_4": ChatGoogleGenerativeAI(

        model="gemini-1.5-flash",

        temperature=0,

        max_tokens=None,

        timeout=None,

        max_retries=3,

        api_key="AIzaSyCit484FnApgyf610Wp6M4vtN7TbuWeubk"
        
    )


}

STATE_FILE = "llm_usage.json"

def load_usage():

    if os.path.exists(STATE_FILE):

        with open(STATE_FILE, "r") as f:

            return json.load(f)
        
    return {"llm_1": 0, "llm_2": 0, "llm_3": 0, "llm_4":0}


def save_usage():

    with open(STATE_FILE, "w") as f:

        json.dump(llm_usage, f)


llm_usage = load_usage()

llm_name = "llm_1"

def swap_llm():

    """Swaps the LLM when usage exceeds the limit and saves the updated state."""
    global llm_name  


    if llm_usage[llm_name] >= 4:

        llm_usage[llm_name] = 0  

        if llm_name == "llm_1":

            llm_name = "llm_2"

        elif llm_name == "llm_2":

            llm_name = "llm_3"

        elif llm_name == "llm_3":

            llm_name = "llm_4"
        
        elif llm_name == "llm_4":
        
            llm_name = "llm_1"


        save_usage() 

    return llm_name
