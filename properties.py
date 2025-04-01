from llms import llm_usage, llms, swap_llm, save_usage

def extract_property_info(previous_results,last_assistant_message,user_response):

    prompt = f"""
    You are an expert property analyst with a deep understanding of Airbnb property data. The user is asking for a detailed explanation of a specific property based on the search results provided. Here is the context:

    1. Previous Results:  
    These are a list of DataFrames containing various details about available properties, such as price, location, amenities, ratings, and reviews:
    {previous_results}

    2. Last Assistant Message:  
    {last_assistant_message}

    3. User Response: 
    {user_response}

    Based on the information above, please provide a detailed, human conversational explanation about the property the user is referring to. Your explanation should include:
    - Key property details (such as price, amenities, location, ratings, etc.) that are available in the dataset.
    - A clear, friendly, and comprehensive description of the property.
    - Any relevant context from the previous results that may help the user better understand the property's features.

    Your answer should be written in a conversational tone that is easy to understand and engaging.
    """

    llm_name = swap_llm()
    llm_usage[llm_name] += 1
    save_usage()
    llm = llms[llm_name]

    response = llm.invoke(prompt).content.strip()

    return response

def extract_property_id(previous_results,last_assistant_message,user_response):
    
    prompt = f"""
        You are a specialized assistant tasked with extracting a property id from the user's input. The property id is a numeric value that uniquely identifies a property and it is available in one of the provided DataFrames in the previous results.
        Based on the information below, identify and output only the property id as a float number without any additional text.

        Previous Results (DataFrames):
        {previous_results}

        Last Assistant Message:
        {last_assistant_message}

        User Response:
        {user_response}
        """
    llm_name = swap_llm()
    llm_usage[llm_name] += 1
    save_usage()
    llm = llms[llm_name]

    response = llm.invoke(prompt).content.strip()
    if '.' in response:  
        return int(response.split('.')[0])
    else:
        return int(response)  
