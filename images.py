from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from database_setup import property_type_values

llm = ChatGoogleGenerativeAI(

        model="gemini-2.0-flash",

        temperature=0,

        max_tokens=None,

        timeout=None,

        max_retries=3,

        api_key="AIzaSyCj02FWwvOF5zEYoA3n6JjhF2NZrBiVBjY"

    )

def follow_up_image(image_data):
    # Define the prompt
    prompt = f"""
    TASK: Analyze the provided image and identify up to two of the following fields that are clearly depicted:
        - property_type (e.g., house, apartment, villa){property_type_values}
        - landscape (e.g., near to beach)
        - view (e.g., forest view, pool view, beach view, farm-view)
        - amenities (e.g., tv, ac, wifi, refrigerator)

    Instructions:
    1. Examine the image and determine which one or two fields are most apparent.
    2. Instead of returning the extracted values as a JSON object, generate a single clarifying question that confirms the user's intent. The question should be based solely on the detected field(s).
    3. If, for example, the image shows a "beach view", the question should be:
    "Are you looking for properties with a beach view, or do you mean properties that are located near the beach?"
    4. If two fields are detected (e.g., property_type and view), ask a question that addresses both without mixing in additional entities.
    5. If no clear fields or ambiguous data is detected, ask a generic clarification question.

    Generate one clear question asking the user to confirm their intended search based on the image without any text or explantion.
    """


    # Create a message with the image and the prompt
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ],
    )

    # Invoke the model with the message
    response = llm.invoke([message])


    return response.content

