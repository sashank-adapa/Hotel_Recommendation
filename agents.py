from database_setup import engine,data_dict_description,unique_category_values,df
from llms import llm_usage, llms, swap_llm, save_usage
import json
import pandas as pd


# Function to classify query based on last assistant message and user response
def classify_query(last_assistant_message,user_response): 

    prompt = f"""
        You are an expert classifier for Airbnb search queries. Your task is to carefully analyze the provided input data and determine which category the user's response belongs to. Follow the guidelines and examples below to ensure accurate classification.

        Categories and Guidelines:

        1. "data_query"
        - Use this category when the user's query filters or searches based on structured dataset attributes that are explicitly available.
        - Example attributes: city, price, number of bedrooms, amenities (e.g., pool, wifi), ratings, and reviews.
        - Example: "Show me listings in New York under $200 per night with free wifi."

        2. "non_data_query"
        - Use this category when the user refers to specific locations or landmarks that are not part of the dataset's attributes.
        - Examples include references such as "near Miami Beach", "close to the Eiffel Tower", or "by Central Park".
        - The dataset does not include these landmark details, so such queries are considered non-data based.
        - Example: "Find properties close to Central Park."

        3. "property_data_query"
        - Use this category when the query is about a specific property or a set of properties, and the question pertains directly to the dataset's columns.
        - Questions might request details such as property reviews, exact price, available amenities, or ratings.
        - Example: "What are the reviews for Property ID 12345?" or "Tell me the price and amenities for this listing."

        4. "property_non_data_query"
        - Use this category when the query focuses on a specific property or properties to know information not provided in the dataset.
        - For instance, if the query asks about the distance of a property from a landmark or requires spatial calculations that the dataset does not cover.
        - Example: "How far is Property ID 67890 from the nearest beach?"

        5. "others"
        - Use this category for queries that do not clearly fall into any of the above. This includes:
            a. Greetings: If the user's message is simply a greeting (e.g., "Hi", "hello", "good morning"), respond with a polite greeting and ask if they need hotel recommendations.
            b. Generic or irrelevant questions: If the query is too vague, generic, or irrelevant to Airbnb property searches, provide a polite, helpful response that may ask for further clarification.
            c. Additional Context Required: If the user's query requires additional context beyond what is provided (for example, if only the last two messages of the conversation are available), classify the query as "others" because it lacks sufficient context.
        - Example: "Can you help me decide from above?" or "What's up?" should be classified as "others".

        Context:
        - The user is actively searching for Airbnb properties.
        - The dataset contains structured information like city, price, amenities, ratings, and reviews but does not include data about nearby landmarks or distances.
        - Input Data provided includes:
            - Last Assistant Question: "{last_assistant_message}"
            - User Response: "{user_response}"
            - Dataset Schema: {data_dict_description}

        Instructions:
        - Review all provided input data and use the guidelines above to classify the query.
        - Be very specific: if the user's query mentions landmarks or spatial relationships not covered by the dataset, choose "non_data_query".
        - If the query is directly related to properties and their dataset details, choose the appropriate property query category.
        - If the query is a greeting, generic inquiry, or lacks sufficient context (for example, when only the last two messages are provided), classify it as "others".
        - Do not include any additional explanation or text in your answer.
        - Your final output should be exactly one of: "data_query", "non_data_query", "property_data_query", "property_non_data_query", or "others".

        Please analyze and classify the user's query accordingly.
        """



    try:
        llm_name = swap_llm()

        llm_usage[llm_name] += 1
        save_usage()

        llm = llms[llm_name]
        response = llm.invoke(prompt).content.strip()
        print(f'Classify Query Response: {response}')
        return response
    except Exception as e:
        print(f"Error in classify_query: {e}")
        return "non_data_query"

 
def extract_data_preferences(last_assistant_message,user_response,filters):

    prompt = f"""
    You are an intelligent Airbnb search filter extractor. Your task is to analyze the conversation history and update the search filters based on the user's latest response.

    Context:
    - The user is searching for Airbnb properties.
    - Update the filters as follows:
        • If the user wants to change an existing filter, update its value.
        • If the user wants to add a new filter, add it to the existing filters.
        • If the user wants to remove or exclude a filter, remove that specific filter.
    - Do not infer missing values; only extract explicitly mentioned filters.

    Input Data:
    - Last Assistant Message: "{last_assistant_message}"
    - User Response: "{user_response}"
    - Dataset Schema: {data_dict_description}
    - Existing Filters: {filters}
    - Unique Category Values: {unique_category_values}

    Instructions:
    1. Extract relevant filters as key-value pairs from the user response.
    2. Use only column names from the dataset schema (data_dict_description) and map user-provided terms to the correct column names. Exclude any filters that do not match any column in the schema.
    3. For the property_type filter, if the user specifies a broad term like "Shared" or "Private", replace it with all matching values from unique_category_values.
    4. For location filters, correct any shortcuts or misspellings using the values provided in Unique Category Values.
    5. Update the existing filters if the user provides new values, add new filters as needed, and remove filters if explicitly requested.
    6. Merge all updates with the existing filters.

    Your final output must be only a JSON object representing the merged updated filters. Do not include any additional text, explanations, or whitespace.
    """




    try:
        llm_name = swap_llm()

        llm_usage[llm_name] += 1
        save_usage()

        llm = llms[llm_name]
        filters = llm.invoke(prompt).content.strip()
        print(f'Extract Data Response: {filters}')
        try:
            # Extract JSON safely
            if "```json" in filters and "```" in filters:
                filters_json_str = filters.split("```json")[1].split("```")[0].strip()
                filters_json = json.loads(filters_json_str)
            else:
                filters_json = json.loads(filters.strip())
        except (json.JSONDecodeError, IndexError):
            filters_json = {}
        return filters_json
    except Exception as e:
        print(f"Error in extract_data_preferences: {e}")
        return {}
    
def filter_data(filters):

    sql_prompt = f"""  
    You are an SQL query generator that converts the given filters into a valid SQL query for filtering an Airbnb dataset.  

    Context:  
    - The database is a SQLite database.  
    - Use the correct column names and values by referring to the following data description:  
    {data_dict_description}  
    - Unique Category Values (use these values for filtering for property_type and location column):
    {unique_category_values} 

    Handle the property_type filter dynamically:  
    - If the user specifies a property type such as "Shared" or "Private" without mentioning explicitly a specific type, replace it with all relevant values from unique_category_values.  
    - For example, "Shared" should include all matching property types related to shared accommodations.  
    - Do the same for other broad terms such as "Private". (check using in operator for multiple categories)
    
    Use the values for location which are provided in the Unique Category Values.If user provided shortcuts or misspelled correct it to match the given values.

    Table Selection:  Use the table properties_df as table name.   
    
    Filters to Apply:  
    {filters}  

    Instructions:  
    1. Generate a valid SQL query using the correct column names.  
    2. Apply the specified filters as WHERE conditions.  
    3. Ensure string values are enclosed in single quotes.  
    4. Use the AND operator to combine multiple filters.  
    5. If a filter requires checking for multiple values, use IN ('value1', 'value2', ...).  
    6. Do not include any explanation, return only the SQL query.  
    7. Use Like clause for amenities and view filters.

    Return only the SQL query without additional text and markdowns.  
    """
    llm_name = swap_llm()

    llm_usage[llm_name] += 1
    save_usage()

    llm = llms[llm_name]
    sql_code = llm.predict(sql_prompt)

    if '```sql' in sql_code and '```' in sql_code:
        sql_code = sql_code.split('```sql')[1].split('```')[0] 

    print(f'Sql code to apply: {sql_code}')

    return pd.read_sql_query(sql_code, engine)

def followup(filters,message_history):

    conversation_history = "\n".join(f"{msg['role'].capitalize()}: {msg['content']}" 
                for msg in message_history
                if msg["role"] in ["user", "assistant"]
                )


    hierarchy = [
        "location",
        "property_type",
        "price",
        "accommodates",
        "number_of_bedrooms",
        "amenities",
        "review_scores_rating",
    ]

    prompt = f"""
    You are assisting a user in filtering Airbnb listings. Your goal is to ask the next most relevant filter question without being repetitive.
    
    Context:
    - Here are the already applied filters: {filters}
    - Follow this dataset schema: {data_dict_description}
    - Prioritize missing filters in this order: {', '.join(hierarchy)}
    - Conversation history: {conversation_history}

    Instructions:
    1. Avoid asking about the same filter multiple times if it has already been discussed.
    2. If a high-priority filter is missing, ask about it naturally without stating "The next most relevant filter question is...".
    3. If all key filters are applied, refine the user's search by asking about preferences naturally (e.g., "Would you like a place with a pool?" instead of forcing a strict filter).
    4. Keep the question conversational and engaging.

    Generate only the next filter question and nothing else.
    """
    llm_name = swap_llm()

    llm_usage[llm_name] += 1
    save_usage()

    llm = llms[llm_name]

    response = llm.predict(prompt)
    print(f'Generated Follow-up Question: {response}')
    return response