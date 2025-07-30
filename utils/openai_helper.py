import json
import os
from openai import OpenAI
from flask import current_app
import logging

# Initialize OpenAI client
def get_openai_client():
    api_key = current_app.config.get('OPENAI_API_KEY')
    if not api_key:
        logging.error("OpenAI API key not found")
        raise ValueError("OpenAI API key is required but not found in environment")
    return OpenAI(api_key=api_key)

def generate_travel_recommendations(query, budget=None, location=None):
    """
    Generate travel recommendations using OpenAI's API based on user query.
    
    Args:
        query (str): User's travel query
        budget (float, optional): User's budget
        location (str, optional): User's location
    
    Returns:
        dict: JSON response with travel recommendations
    """
    try:
        client = get_openai_client()
        
        # Construct a detailed prompt
        system_prompt = """
        You are TravelMindal AI, an expert travel assistant who specializes in budget-friendly travel planning.
        You provide detailed, practical travel recommendations based on the user's budget and location.
        Your responses should include:
        1. A brief summary of what's possible with the given budget
        2. 3-5 specific activities or places to visit with approximate costs
        3. Practical tips for maximizing the budget (transport, food options, etc.)
        4. A suggested time allocation (e.g., half-day itinerary, full-day plan)
        
        Format your response as a JSON object with the following structure:
        {
            "summary": "Brief overview of what's possible with the budget",
            "activities": [
                {
                    "name": "Activity name",
                    "description": "Brief description",
                    "cost": "Approximate cost",
                    "location": "Location details"
                }
            ],
            "tips": ["Tip 1", "Tip 2", "Tip 3"],
            "time_allocation": "Suggested time plan"
        }
        """
        
        # Construct the user message with all available information
        user_message = query
        if budget:
            user_message += f"\nMy budget is {budget}."
        if location:
            user_message += f"\nI'm in {location}."
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # Parse the response and return as JSON
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logging.error(f"Error generating travel recommendations: {str(e)}")
        return {
            "error": "Failed to generate travel recommendations",
            "details": str(e)
        }

def generate_itinerary(location, budget, duration=1, interests=None):
    """
    Generate a complete travel itinerary using OpenAI's API.
    
    Args:
        location (str): Destination for the itinerary
        budget (float): Available budget
        duration (int, optional): Duration in days
        interests (list, optional): List of user interests
    
    Returns:
        dict: JSON response with detailed itinerary
    """
    try:
        client = get_openai_client()
        
        # Construct a detailed prompt
        system_prompt = """
        You are TravelMindal AI, an expert travel assistant who creates detailed itineraries.
        Create a comprehensive daily itinerary based on the user's location, budget, duration and interests.
        Your response should include:
        1. A day-by-day breakdown of activities
        2. Estimated costs for each activity, meal, and transportation
        3. Specific places to visit with brief descriptions
        4. Practical logistical details (transportation between places, etc.)
        5. Meal recommendations (breakfast, lunch, dinner)
        
        Format your response as a JSON object with the following structure:
        {
            "destination": "Location name",
            "budget_summary": {
                "total": total budget amount,
                "accommodation": accommodation cost,
                "food": food cost,
                "activities": activities cost,
                "transportation": transportation cost,
                "other": other costs
            },
            "days": [
                {
                    "day": day number,
                    "date": "date if provided",
                    "activities": [
                        {
                            "time": "time slot",
                            "name": "activity name",
                            "description": "brief description",
                            "location": "location details",
                            "cost": estimated cost,
                            "duration": "duration in hours/minutes",
                            "transportation": "how to get there"
                        }
                    ],
                    "meals": [
                        {
                            "type": "breakfast/lunch/dinner",
                            "suggestion": "suggested place/food",
                            "cost": estimated cost
                        }
                    ],
                    "total_day_cost": total cost for the day
                }
            ],
            "tips": ["Tip 1", "Tip 2", "Tip 3"]
        }
        """
        
        # Construct the user message with all available information
        user_message = f"Please create an itinerary for {location} with a budget of {budget}."
        if duration > 1:
            user_message += f" The trip will be {duration} days long."
        else:
            user_message += " The trip will be for 1 day."
            
        if interests:
            user_message += f" My interests include: {', '.join(interests)}."
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        # Parse the response and return as JSON
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        logging.error(f"Error generating itinerary: {str(e)}")
        return {
            "error": "Failed to generate itinerary",
            "details": str(e)
        }

def chat_with_travel_assistant(message, chat_history=None):
    """
    Have a conversation with the travel assistant using OpenAI's API.
    
    Args:
        message (str): User's message
        chat_history (list, optional): List of previous messages in the format
                                      [{"role": "user", "content": "msg"}, ...]
    
    Returns:
        str: AI assistant's response
    """
    try:
        client = get_openai_client()
        
        # Set up the system message
        system_message = """
        You are TravelMindal AI, a friendly and knowledgeable travel assistant.
        You help users plan their travel by providing information about destinations,
        activities, accommodations, transportation, and budgeting.
        Keep your responses concise but informative, focusing on practical travel advice.
        If you don't know the answer to a specific question, be honest about it but try to
        provide general guidance that might still be helpful.
        """
        
        # Prepare the messages for the API call
        messages = [{"role": "system", "content": system_message}]
        
        # Add chat history if provided
        if chat_history:
            messages.extend(chat_history)
        
        # Add the current user message
        messages.append({"role": "user", "content": message})
        
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logging.error(f"Error chatting with travel assistant: {str(e)}")
        return f"I'm sorry, I encountered an error while processing your request. Please try again later. Error: {str(e)}"
