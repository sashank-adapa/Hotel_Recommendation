from llms import llm_usage, llms, swap_llm, save_usage



def result_summarizer(property_row, message_history):
    """
    Generates a concise summary for a single Airbnb property based on the user's preferences.
    """
    try:
        # Extract only user and assistant messages from session history
        conversation_history = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}" 
            for msg in message_history if msg["role"] in ["user", "assistant"]
        )

        # Format the property details
        formatted_property_str = "\n".join(
            f"{col}: {property_row[col]}" for col in property_row.index
        )

        print(f'Property details:\n{formatted_property_str}')

        # Construct the LLM prompt
        prompt = f"""
        You are an expert in property analysis. Your task is to generate a concise summary for an Airbnb property based on the user's preferences.

        User Preferences from Conversation History:
        {conversation_history}

        Task Instructions:
        - Extract and focus on the most relevant attributes mentioned by the user.
        - Ensure the summary is clear, concise, and structured.
        - Focus on these key attributes:
          • Distance (if available, otherwise exclude)
          • Amenities (as specified by the user)
          • Any other criteria specified by the user
        - Generate very concise bullet points that explain the property's key features using information from the 'description' and 'neighborhood_overview' fields.
        - Avoid assumptions or unnecessary details.

        Airbnb Property Data:
        {formatted_property_str}

        Now, generate a structured and informative summary for this property.
        """

        llm_name = swap_llm()
        llm_usage[llm_name] += 1
        save_usage()
        llm = llms[llm_name]

        return llm.invoke(prompt).content.strip()

    except Exception as e:
        print(f"Error in result_summarizer_single_property: {e}")
        return "Sorry, I couldn't generate a summary at the moment."

    

def genric_summarizer(message_history,extra_info = ''):
    conversation_history = "\n".join(
        f"{msg['role'].capitalize()}: {msg['content']}" 
        for msg in message_history if msg["role"] in ["user", "assistant"]
    ) + extra_info
    
    prompt = f"""
    You are an intelligent conversation summarizer and responder with access to the full conversation history and any additional extra information provided. Your task is to generate a helpful, polite, and context-aware answer to the user's latest message. Please follow these guidelines:

    1. If the user's latest message is a greeting (e.g., "hi", "hello", "good morning"), respond with a polite greeting and ask if they need any hotel recommendations.
    2. If the user's latest message is irrelevant or generic without clear context, provide a polite and helpful response that may gently prompt for more details or refer to the conversation history.
    3. If the user's message is generic or lacks context, review the entire conversation history to generate a response that addresses their needs appropriately.
    4. Always ensure your response is engaging, polite, and tailored to the context of the conversation.

    Conversation History:
    {conversation_history}

    Please generate your response below:
    """
    
    llm_name = swap_llm()
    llm_usage[llm_name] += 1
    save_usage()
    llm = llms[llm_name]

    response = llm.invoke(prompt).content.strip()

    return response

