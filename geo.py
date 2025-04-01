from llms import llm_usage, llms, swap_llm, save_usage
from geopy.distance import geodesic
import pandas as pd

def extract_coordinates_from_query(message_history):
    try:
        # Extract conversation history (only user and assistant messages)
        conversation_history = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}" 
            for msg in message_history if msg["role"] in ["user", "assistant"]
        )

        prompt = f"""
        Extract the latitude and longitude of the most relevant location mentioned in the last user query.  
        
        User Query: 
        Consider the last message from the user in the conversation history as the primary location reference.  

        Handling Missing Locations:  
        - If the last user query does not specify a location, check the previous conversation history to find the **most recently validated location** mentioned by the assistant.  
        - If the query includes a **specific place** (e.g., 'San Francisco Airport' or 'Miami Beach'), extract the exact coordinates for that place rather than the city.  

        **Conversation History for Context:**  
        {conversation_history}

        **Output Format:**  
        - Strictly return the coordinates in the format (lat, lon) in WGS84 projection.  
        - No additional text, explanations, or extra characters.  

        **Example Outputs:**  
        (37.7749, -122.4194)  
        (25.7617, -80.1918)  
        """

        # Invoke LLM
        llm_name = swap_llm()
        llm_usage[llm_name] += 1
        save_usage()
        llm = llms[llm_name]

        response = llm.invoke(prompt).content.strip()

        # Extract and validate coordinates
        coordinates_list = response.strip('()').split(',')
        coordinates_tuple = tuple(map(float, coordinates_list))
        return coordinates_tuple

    except Exception as e:
        print(f"Error in extract_coordinates_from_query: {e}")
        return (0.0, 0.0)  # Default return if error occurs

        
    
def extract_location_from_query(message_history):
    try:
        # Extract conversation history (only user and assistant messages)
        conversation_history = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}" 
            for msg in message_history if msg["role"] in ["user", "assistant"]
        )

        prompt = f"""
        Extract the city name from the user's message while considering past context.

        Rules:
        - If the latest user message contains a city from ['San Francisco', 'New Jersey', 'Seattle', 'Oslo', 'Singapore', 'Tokyo', 'Taipei'], return that city.
        - If the message contains only a general place (e.g., airport, beach, downtown), refer to the most recent validated city mentioned by the user in previous messages.
        - Only return one of the following cities: 'San Francisco', 'New Jersey', 'Seattle', 'Oslo', 'Singapore', 'Tokyo', or 'Taipei'.
        - If no valid city is found, return 'NA'.

        Conversation History:
        {conversation_history}

        Expected Output:
        - A single city name: 'San Francisco', 'New Jersey', 'Seattle', 'Oslo', 'Singapore', 'Tokyo', or 'Taipei'.
        - If no valid city is identified, return 'NA'.
        - Do not include any extra text, explanations, or formatting.

        Example Inputs and Outputs:
        - User: "I am looking for properties in San Francisco." → Output: "San Francisco"
        - User: "Can I find something near the airport?" (Previously mentioned 'Seattle') → Output: "Seattle"
        - User: "I want a stay near Charminar." → Output: "NA"
        """

        # Invoke LLM
        llm_name = swap_llm()
        llm_usage[llm_name] += 1
        save_usage()
        llm = llms[llm_name]

        response = llm.invoke(prompt).content.strip()

        # Ensure response is valid and within allowed cities
        valid_cities = {'San Francisco', 'New Jersey', 'Seattle', 'Oslo', 'Singapore', 'Tokyo', 'Taipei'}
        return response if response in valid_cities else "NA"

    except Exception as e:
        print(f"Error in extract_location_from_query: {e}")
        return "NA"  # Default return in case of error

    
def calculate_distance_to_key_place(row, key_place_coords):
    """
    Calculates the geodesic distance between a row's coordinates and a key place.
    """
    if key_place_coords is None or pd.isna(row['latitude']) or pd.isna(row['longitude']):
        return None  # Handle missing coordinates

    lat_1, long_1 = key_place_coords
    lat_2, long_2 = row['latitude'], row['longitude']

    coords_1 = (lat_1, long_1)
    coords_2 = (lat_2, long_2)

    return geodesic(coords_1, coords_2).kilometers    

# Function to filter the dataset, compute the distance between the properties and map-mark
def filter_compute_distances(df,location,map_point):
    
    # Filter the dataframe based on the location mentioed by the user
    filtered_df = df[df['location']==location].copy()

    # Compute the distance for each row in the filtered DataFrame
    filtered_df['Distance'] = filtered_df.apply(lambda row:round(calculate_distance_to_key_place(row,map_point),3),axis=1)
    
    filtered_df = filtered_df.sort_values(by=['Distance'],ascending=True)

    # Return the DataFrame with the computed distance column
    return filtered_df