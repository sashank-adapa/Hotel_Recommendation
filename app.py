import streamlit as st
import pandas as pd
import json
import datetime
import base64
from PIL import Image
from geopy.distance import geodesic
import cv2
import requests
import numpy as np
import ast
import math
import uuid

# Import external modules (ensure these modules exist in your project)
from database_setup import engine, df
from images import follow_up_image
from agents import (
    classify_query,
    extract_data_preferences,
    filter_data,
    followup
)
from summarizers import result_summarizer, genric_summarizer
from geo import extract_coordinates_from_query, extract_location_from_query, filter_compute_distances
from properties import extract_property_info, extract_property_id

# Ensure st.set_page_config() is the first Streamlit command
st.set_page_config(page_title="Trip planner", page_icon=":hotel:", layout="wide")


# Add popular destinations function
def add_popular_destinations():
    st.markdown("""
        <style>
            .destination-container {
                position: relative;
                overflow: hidden;
                transition: transform 0.3s ease-in-out;
                border-radius: 10px;
            }
            
            .destination-container:hover {
                transform: scale(1.05);
            }
            
            .destination-image {
                width: 100%;
                height: 250px;
                object-fit: cover;
                border-radius: 10px;
            }
            
            .destination-text {
                font-size: 16px;
                font-weight: bold;
                text-align: center;
                margin-top: 10px;
                color: black;
            }
            
            .destination-desc {
                font-size: 14px;
                text-align: center;
                color: black;
            }
            
            /* Style for the Explore button */
            .explore-button {
                display: block;
                width: 100%;
                text-align: center;
                background-color: #4CAF50; 
                color: white !important;
                padding: 10px;
                border-radius: 5px;
                text-decoration: none;
                font-weight: bold;
                margin-top: 10px;
            }

            .explore-button:hover {
                background-color: #c70039; /* Darker red on hover */
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h4 style='color: black; text-align: center;'>Popular Destinations</h4>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    destinations = [
        {
            "name": "New Jersey",
            "description": "Atlantic City Boardwalk",
            "column": col1,
            "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0b/50/3d/4c/atlantic-city-boardwalk.jpg?w=1800&h=1000&s=1",
            "wiki": "https://en.wikipedia.org/wiki/New_Jersey"
        },
        {
            "name": "Seattle",
            "description": "Space Needle",
            "column": col2,
            "image": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/1b/58/7d/b0/photo0jpg.jpg?w=1200&h=700&s=1",
            "wiki": "https://en.wikipedia.org/wiki/Seattle"
        },
        {
            "name": "San Francisco",
            "description": "Golden Gate Bridge",
            "column": col3,
            "image": "https://images.pexels.com/photos/821679/pexels-photo-821679.jpeg?auto=compress&cs=tinysrgb&w=600",
            "wiki": "https://en.wikipedia.org/wiki/San_Francisco"
        }
    ]
    
    for dest in destinations:
        with dest['column']:
            st.markdown(f"""
                <div class="destination-container">
                    <img src="{dest['image']}" class="destination-image">
                </div>
                <p class="destination-text">{dest['name']}</p>
                <p class="destination-desc">{dest['description']}</p>
                <a href="{dest['wiki']}" class="explore-button" target="_blank">Explore {dest['name']}</a>
            """, unsafe_allow_html=True)

# Function to save search history
def save_search_history(search_params):
    try:
        # Try to load existing history
        try:
            with open('search_history.json', 'r') as f:
                search_history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            search_history = []
        
        # Add current search (with timestamp)
        import datetime
        search_params['timestamp'] = datetime.datetime.now().isoformat()
        
        # Limit history to last 10 searches
        search_history.append(search_params)
        search_history = search_history[-10:]
        
        # Save updated history
        with open('search_history.json', 'w') as f:
            json.dump(search_history, f)
    except Exception as e:
        st.error(f"Error saving search history: {e}")

# Function to load search history
def load_search_history():
    try:
        with open('search_history.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    
# Function to recommend properties with enhanced filtering
def recommend_properties(user_preferences, properties_df):
    # Create a copy of the properties DataFrame
    filtered_properties = properties_df.copy()

    # Destination filter with more flexible matching
    if user_preferences.get("destination"):
        filtered_properties = filtered_properties[
            filtered_properties["location"].str.contains(user_preferences["destination"], case=False, na=False)
        ]

    # Budget filter
    if user_preferences.get("budget"):
        filtered_properties = filtered_properties[filtered_properties["price"] <= user_preferences["budget"]]

    # Amenities filter with case-insensitive, partial matching
    if user_preferences.get("amenities") and len(user_preferences["amenities"]) > 0:
        # Ensure ALL selected amenities are present (case-insensitive)
        amenities_condition = filtered_properties['amenities'].apply(
            lambda x: all(amenity.lower() in str(x).lower() for amenity in user_preferences["amenities"])
        )
        filtered_properties = filtered_properties[amenities_condition]

    # Guest capacity filter using 'accommodates'
    if user_preferences.get("guests"):
        filtered_properties = filtered_properties[filtered_properties["accommodates"] >= user_preferences["guests"]]

    # Sorting with fallback
    try:
        # Sort by Total_reviews_score if available
        return filtered_properties.sort_values(by='Total_reviews_score', ascending=False).head(5)
    except KeyError:
        # If no review score column, return top 5 as is
        return filtered_properties.head(5)    
    
# Custom CSS 
st.markdown("""
<style>
/* General Page Styling */
body {
    background: white;
    min-height: 100vh;
    margin: 0;
    padding: 20px;
    color: black;
}
            

/* Streamlit App Background */
.stApp {
    background-color: transparent;
}

/* Header Styling */
.header-container {
    position: relative;
    color: white;
    padding: 50px 20px;
    text-align: center;
    border-radius: 10px;
    margin-bottom: 20px;
    background-image: url('https://thumbs.dreamstime.com/b/luxury-hotel-room-master-bedroom-creative-ai-design-background-instagram-facebook-wall-painting-photo-wallpaper-backgrounds-325040660.jpg');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-blend-mode: overlay;
    overflow: hidden;
    transition: transform 0.3s ease;
}

.header-container:hover {
    transform: scale(1.02);
    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.header-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 1;
}

.header-container h1 {
    position: relative;
    z-index: 2;
    font-size: 3rem;
    margin-bottom: 15px;
    font-weight: bold;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
    transition: transform 0.3s ease;
}

.header-container:hover h1 {
    transform: scale(1.05);
}

.header-container h2 {
    position: relative;
    z-index: 2;
    font-size: 1.5rem;
    font-weight: normal;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
    transition: transform 0.3s ease;
}

.header-container:hover h2 {
    transform: scale(1.05);
}

/* Labels and Input Fields */
label, .stText, .stSelectbox label, .stNumberInput label, .stDateInput label, .stSlider label {
    color: black !important;
    font-weight: bold;
}

/* General Input Styling */
.stTextInput>div>div>input, 
.stNumberInput>div>div>input, 
.stSelectbox>div>div>div, 
.stMultiSelect>div>div>div {
    background-color: white !important;
    color: black !important;
    border: 1px solid #e0e0e0 !important;
    transition: all 0.3s ease;
}

.stTextInput>div>div>input:hover,
.stNumberInput>div>div>input:hover,
.stSelectbox>div>div>div:hover,
.stMultiSelect>div>div>div:hover {
    border-color: #4CAF50 !important;
    box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.2);
}

/* Slider Text Color */
.stSlider label, .stSlider div {
    color: black !important;
}

/* Placeholder Text Styling */
::placeholder {
    color: black !important;
}

/* Chat Input: Black Background, White Placeholder */
.stChatInput textarea {
    background-color: black !important;
    color: white !important; 
    border: 1px solid #e0e0e0 !important;
}

/* Change Placeholder Text to White */
.stChatInput textarea::placeholder {
    color: white !important;
    opacity: 1 !important;
}

/* Destination Grid Styling */
.destination-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
}

/* Destination Card Styling */
.destination-card {
    position: relative;
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: all 0.3s ease-in-out;
}

.destination-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(to bottom, transparent 60%, rgba(0,0,0,0.7));
    opacity: 0;
    transition: opacity 0.3s ease-in-out;
    z-index: 1;
}

.destination-card:hover {
    transform: scale(1.05);
    box-shadow: 0 10px 20px rgba(0,0,0,0.2);
}

.destination-card:hover::before {
    opacity: 1;
}

.destination-card img {
    width: 100%;
    height: 250px;
    object-fit: cover;
    transition: transform 0.3s ease-in-out, filter 0.3s ease-in-out;
}

.destination-card:hover img {
    transform: scale(1.1);
    filter: brightness(0.8);
}

.destination-card .overlay-text {
    position: absolute;
    bottom: -100%;
    left: 0;
    width: 100%;
    padding: 15px;
    background: rgba(0,0,0,0.7);
    color: white;
    transition: bottom 0.3s ease-in-out;
    z-index: 2;
}

.destination-card:hover .overlay-text {
    bottom: 0;
}

/* Buttons */
.stButton>button {
    background-color: #4CAF50 !important;
    color: white !important;
}

.stButton>button:hover {
    background-color: #45a049 !important;
}
            
.custom-white-text {
            color: white !important;
            font-weight: bold;
            text-align: center;
        }

.streamlit-container {
    transition: transform 0.3s ease;
}

.streamlit-container:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* Ensure chat messages are black */
.stChatMessage {
    color: black !important;
}

/* Styling for user and assistant messages */
.stChatMessage-user {
    background-color: #f0f0f0;
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 10px;
    transition: transform 0.3s ease;
}

.stChatMessage-user:hover {
    transform: scale(1.02);
}

.stChatMessage-assistant {
    background-color: #e6e6e6;
    border-radius: 10px;
    padding: 10px;
    margin-bottom: 10px;
    transition: transform 0.3s ease;
}

.stChatMessage-assistant:hover {
    transform: scale(1.02);
}

/* Ensure text is black within chat messages */
.stChatMessage p {
    color: black !important;
}

/* Additional styling to enhance readability */
.stChatMessage code {
    background-color: #f4f4f4;
    color: black;
    padding: 2px 4px;
    border-radius: 4px;
} 

/* General Text Color */
body, .stMarkdown, .stText, .stTextInput, .stSelectbox, .stNumberInput, .stDateInput, .stSlider {
    color: black !important;
}

/* Explicit Text Color Overrides */
.stMarkdown p, 
.stMarkdown span, 
.stTextInput>div>div>input, 
.stNumberInput>div>div>input, 
.stSelectbox>div>div>div, 
.stMultiSelect>div>div>div,
.stText,
.stChatMessage{
    color: black !important;
}       

.stChatInput textarea {
    color: White !important;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
    .header-container h1 {
        font-size: 2rem;
    }
    
    .header-container h2 {
        font-size: 1.2rem;
    }
    
    .destination-grid {
        grid-template-columns: 1fr;
    }
}

/* Smooth Scroll Behavior */
html {
    scroll-behavior: smooth;
}
</style>
""", unsafe_allow_html=True)


# Dashboard function
def show_dashboard():
    st.markdown(f"""
    <div class="header-container">
        <h1>VayCation.Ai</h1>
        <h2>Book your stay with Trip Planner</h2>
    </div>
    """, unsafe_allow_html=True)

    # Add Popular Destinations Section
    add_popular_destinations()

# -----------------------------
# Initialize Session State
# -----------------------------

def update_message_history(role, content):
    st.session_state.message_history.append({"role": role, "content": content})


if "message_history" not in st.session_state:
    st.session_state.message_history = []
    update_message_history("assistant", "How can I help you today?")

if "filters" not in st.session_state:
    st.session_state.filters = {}  # Stores extracted search filters

if "filter_df" not in st.session_state:
    st.session_state.filter_df = pd.DataFrame()

if "result_dfs" not in st.session_state:  # used for property-level enquiry
    st.session_state.result_dfs = []

if "geo_pres" not in st.session_state:
    st.session_state.geo_pres = False

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "prev_res_df" not in st.session_state:
    st.session_state.prev_res_df = pd.DataFrame()


# Main Streamlit App
def main():
    # Initialize session state for dashboard visibility
    if 'show_dashboard' not in st.session_state:
        st.session_state.show_dashboard = True

    # Create a placeholder for the dashboard
    placeholder_dashboard = st.empty()

    # Sidebar (unchanged)
    with st.sidebar:
        st.title("Trip Planner Menu")

        # Home button
        if st.button("🏠 Home", use_container_width=True):
            # Reset dashboard and chat history
            st.session_state.show_dashboard = True
            st.session_state.message_history = []
            st.session_state.filters = {}
            st.session_state.filter_df = pd.DataFrame()
            st.session_state.result_dfs = []
            st.session_state.geo_pres = False
            st.session_state.uploaded_image = None
            st.session_state.prev_res_df = pd.DataFrame()
            st.rerun()

        # Inject Custom CSS to Force White Text
        st.markdown("""
            <style>
                .custom-white-text {
                    color: white !important;
                    font-weight: bold;
                    text-align: center;
                }
            </style>
        """, unsafe_allow_html=True)

        # Search History Section
        st.header("Planning History")
        search_history = load_search_history()

        if search_history:
            for idx, search in enumerate(reversed(search_history), 1):
                with st.expander(f"Search {idx}"):
                    st.write(f"**Destination:** {search.get('destination', 'N/A')}")
                    st.write(f"**Budget:** ${search.get('budget', 'N/A')}")
                    st.write(f"**Guests:** {search.get('guests', 'N/A')}")
                    st.write(f"**Timestamp:** {search.get('timestamp', 'N/A')}")
        else:
            st.markdown("<p class='custom-white-text'>No recent searches</p>", unsafe_allow_html=True)

        # Settings and Help Sections (unchanged)
        st.header("Settings")
        st.markdown("""
            <div style='color: white; font-weight: bold !important;'>TBD</div>
        """, unsafe_allow_html=True)
        st.info("Personalization and preferences will be added in future updates.")

        st.header("Help")
        st.markdown("""
            <div style='color: white; font-weight: bold !important;'>Coming Soon</div>
        """, unsafe_allow_html=True)
        st.info("Comprehensive guide and support resources will be available soon.")

        st.markdown("---")
        st.markdown("""
            <div style='color: white; font-weight: bold !important;'>VayCation 1.0</div>
        """, unsafe_allow_html=True)
        st.markdown("""
            <div style='color: white; font-weight: bold !important;'>*Explore. Book. Enjoy.*</div>
        """, unsafe_allow_html=True)

    # Main content area
    with placeholder_dashboard.container():
        # Show dashboard if flag is True
        if st.session_state.show_dashboard:
            show_dashboard()

        # Chatbot Section
        st.markdown("""
        <hr style="border: 1px solid #ccc;">
        <h3 style='color: black;'>AI Powered Travel Planner</h3>
        """, unsafe_allow_html=True)

        # File uploader
        uploaded_image = st.file_uploader("Upload an image to find similar type of rooms.", type=["png", "jpg", "jpeg"])

        if uploaded_image is not None:
            uploaded_image.seek(0)
            image_data = base64.b64encode(uploaded_image.read()).decode("utf-8")

            # Display the image
            uploaded_image.seek(0)  # Reset pointer
            image = Image.open(uploaded_image)
            st.image(image)

            # Custom black caption
            st.markdown(
                "<p style='text-align: center; color: black; font-size: 16px;'>Uploaded Image</p>",
                unsafe_allow_html=True
            )

            if st.session_state.uploaded_image != uploaded_image:
                follow_up = follow_up_image(image_data)
                update_message_history("assistant", follow_up)
                st.session_state.uploaded_image = uploaded_image

        # Display chat messages
        for message in st.session_state.message_history:
            with st.chat_message(message["role"]):
                if isinstance(message["content"], list):  # Handle structured messages
                    for property_info in message["content"]:
                        col1, col2 = st.columns([1, 2])

                        with col1:
                            # Display property image if available
                            try:
                                response = requests.get(property_info['picture_url'], timeout=5, verify=False)
                                if response.status_code == 200:
                                    image_arr = np.asarray(bytearray(response.content), dtype=np.uint8)
                                    img = cv2.imdecode(image_arr, cv2.IMREAD_COLOR)
                                    st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
                                else:
                                    st.write("Image not available")
                            except Exception as e:
                                st.write("Image not available")

                        with col2:
                            # Display property details
                            st.markdown(
                            f"<h2 style='color: var(--primaryColor);'>{property_info["name"]}</h2>",
                            unsafe_allow_html=True
                        )
                            st.write(property_info["summary"])
                            st.write(f"**Location:** {property_info['location']}")
                            if property_info.get("distance") is not None:
                                st.write(f"**Distance (Miles):** {property_info['distance']}")
                            st.write(f"**Price:** ${property_info['price']} per night")
                            st.write(f"**Amenities:** {property_info['amenities']} etc...")
                            st.write(f"**Reviews:** {property_info['reviews']}")
                            st.write(f"**Max Guests:** {property_info['max_guests']}")

                            st.markdown(
                            f"""
                            <a href="{property_info['url']}" target="_blank">
                            <button style="
                                background-color: green; 
                                color: white; 
                                border: none; 
                                padding: 10px 20px; 
                                border-radius: 5px;
                                cursor: pointer;">
                                Book {property_info['name']}
                            </button>
                            </a>
                            """,
                            unsafe_allow_html=True
                        )
            

                else:
                    # Display regular text messages
                    st.markdown(message["content"])

    # Chat input - placed outside the main container to ensure it stays at the bottom
    user_input = st.chat_input("Plan your vacation with AI !")

    if user_input:
        update_message_history("user", user_input)

        with st.chat_message("user"):
            st.markdown(user_input)

        # Retrieve the last two messages for context
        message_history = st.session_state.message_history
        user_response = st.session_state.message_history[-1]["content"]

        query_type = classify_query(message_history, user_response)

        if query_type == "data_query":
            existing_filters = st.session_state.filters
            filters = extract_data_preferences(message_history, user_response, existing_filters)
            st.session_state.filters = filters
            st.session_state.filter_df = filter_data(filters)

            if st.session_state.filter_df.shape[0] > 50:
                assistant_question = followup(st.session_state.filters, st.session_state.message_history)
                with st.chat_message("assistant"):
                    st.markdown(assistant_question)
                update_message_history("assistant", assistant_question)
            else:
                properties = st.session_state.filter_df.sort_values('review_scores_rating', ascending=False).head(5)
                if properties.empty:
                    with st.chat_message("assistant"):
                        st.markdown(genric_summarizer(st.session_state.message_history,
                                                      f'No Properties Available. Please change your preferences: {st.session_state.filters}'))
                    update_message_history("assistant", genric_summarizer(st.session_state.message_history,
                                                      f'No Properties Available. Please change your preferences: {st.session_state.filters}'))
                else:
                    st.session_state.result_dfs.append(properties)

        elif query_type == 'non_data_query':
            coordinates = extract_coordinates_from_query(st.session_state.message_history)
            location = extract_location_from_query(st.session_state.message_history)

            if (not isinstance(coordinates, tuple) or len(coordinates) != 2 or coordinates == (0.0, 0.0) or location == 'NA'):
                with st.chat_message("assistant"):
                    st.markdown("Sorry, can you choose the location from San Francisco, New Jersey, Seattle, Oslo, Singapore, Tokyo or Taipei?")
                update_message_history("assistant", "Sorry, can you choose the location from San Francisco, New Jersey, Seattle, Oslo, Singapore, Tokyo or Taipei?")
            else:
                distance_df = filter_compute_distances(df, location, coordinates)
                if st.session_state.geo_pres:
                    st.session_state.filter_df = filter_data(st.session_state.filters)
                if st.session_state.filter_df.empty:
                    st.session_state.filter_df = distance_df
                else:
                    st.session_state.filter_df = st.session_state.filter_df.merge(
                        distance_df[['id', 'Distance']], on='id', how='inner'
                    )
                st.session_state.geo_pres = True
                properties = st.session_state.filter_df.sort_values(['Distance', 'review_scores_rating'],
                                                                    ascending=[True, False]).head(5)
                if properties.empty:
                    with st.chat_message("assistant"):
                        st.markdown(genric_summarizer(st.session_state.message_history,
                                                      f'No Properties Available. Please change your preferences: {st.session_state.filters}'))
                    update_message_history("assistant", genric_summarizer(st.session_state.message_history,
                                                      f'No Properties Available. Please change your preferences: {st.session_state.filters}'))
                else:
                    st.session_state.result_dfs.append(properties)

        elif query_type == 'property_data_query':
            response = extract_property_info(st.session_state.result_dfs,
                                                st.session_state.message_history,
                                                st.session_state.message_history[-1]["content"])
            with st.chat_message("assistant"):
                st.markdown(response)
            update_message_history("assistant", response)

        elif query_type == 'property_non_data_query':
            prop_id = extract_property_id(st.session_state.result_dfs,
                                            st.session_state.message_history,
                                            st.session_state.message_history[-1]["content"])

            try:
                row = df[df['id'].astype(int) == prop_id]
                prop_coords = (row['latitude'].iloc[0], row['longitude'].iloc[0])
                dest_coords = extract_coordinates_from_query(st.session_state.message_history)
                distance = geodesic(prop_coords, dest_coords).kilometers
                info = f'It is {distance:.2f} kms away.'
                response = genric_summarizer(st.session_state.message_history, info)
                with st.chat_message("assistant"):
                    st.markdown(response)
                update_message_history("assistant", response)
            except Exception as e:
                update_message_history("assistant", "Unable to get the distance at the moment. Please try again after some time.")

        else:
            response = genric_summarizer(st.session_state.message_history, '')
            with st.chat_message("assistant"):
                st.markdown(response)
            update_message_history("assistant", response)
        

        # Check if we need to display property cards as part of the conversation
        if ('result_dfs' in st.session_state and 
            st.session_state.result_dfs and 
            (st.session_state.prev_res_df.empty or 
            not st.session_state.result_dfs[-1].equals(st.session_state.prev_res_df))):

            with st.chat_message("assistant"):
                recommended_properties = st.session_state.result_dfs[-1]
                message_content = []  # List to store structured message content

                for index, property_row in recommended_properties.iterrows():
                    col1, col2 = st.columns([1, 2])
                    property_message = {}

                    with col1:
                        # Display property image
                        try:
                            response = requests.get(property_row['picture_url'], timeout=5, verify=False)
                            if response.status_code == 200:
                                image_arr = np.asarray(bytearray(response.content), dtype=np.uint8)
                                img = cv2.imdecode(image_arr, cv2.IMREAD_COLOR)
                                st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), use_container_width=True)
                            else:
                                st.write("Image not available")
                        except Exception as e:
                            st.write("Image not available")

                    with col2:
                        st.markdown(
                            f"<h2 style='color: var(--primaryColor);'>{property_row['name']}</h2>",
                            unsafe_allow_html=True
                        )

                        summary = result_summarizer(property_row, st.session_state.message_history)
                        st.write(summary)
                        st.write(f"**Location:** {property_row['location']}")
                        if 'Distance' in property_row.index:
                            st.write(f"**Distance (Miles):** {property_row['Distance']}")
                        st.write(f"**Price:** ${property_row['price']} per night")
                        st.write(f"**Amenities:** {list(set(item for item in ast.literal_eval(property_row['amenities'])))[:5]} etc...")
                        st.write(f"**Reviews:** {property_row['review_scores_rating']}")
                        st.write(f"**Max Guests:** {property_row['accommodates']}")

                        # Store all this information in a structured format
                        property_message = {
                            "name": property_row['name'],
                            "summary": summary,
                            "location": property_row['location'],
                            "distance": property_row['Distance'] if 'Distance' in property_row.index else None,
                            "price": property_row['price'],
                            "amenities": list(set(item for item in ast.literal_eval(property_row['amenities'])))[:5],
                            "reviews": property_row['review_scores_rating'],
                            "max_guests": property_row['accommodates'],
                            "picture_url":property_row['picture_url']
                        }

                        # Save button information
                        st.markdown(
                            f"""
                            <a href="{property_row['listing_url']}" target="_blank">
                            <button style="
                                background-color: green; 
                                color: white; 
                                border: none; 
                                padding: 10px 20px; 
                                border-radius: 5px;
                                cursor: pointer;">
                                Book {property_row['name']}
                            </button>
                            </a>
                            """,
                            unsafe_allow_html=True
                        )
                        property_message["url"] = property_row["listing_url"]

                    # Append the structured message for this property
                    message_content.append(property_message)

                # Store the assistant message as an exact structured response in history
                update_message_history("assistant", message_content)

                st.session_state.prev_res_df = st.session_state.result_dfs[-1]

# Run the app
if __name__ == "__main__":
    main()
