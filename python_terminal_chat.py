import requests
import sys
import os

# Set your backend URL
BASE_URL = "http://127.0.0.1:8000"

def chat_with_model():
    print("Welcome to the Math Buddy Bot Terminal!")
    print("Type 'exit' to quit the chat.")
    
    # Start a new session
    try:
        response = requests.post(f"{BASE_URL}/start_session")
        if response.status_code == 200:
            session_id = response.json()['session_id']
            print(f"Started new session with ID: {session_id}")
        else:
            print("Failed to start a new session. Exiting.")
            return
    except requests.exceptions.RequestException as e:
        print(f"Error starting a new session: {e}")
        return

    while True:
        # Get user input
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        # Send the input to the backend's /chat endpoint
        try:
            response = requests.post(f"{BASE_URL}/chat", 
                                     json={"message": user_input}, 
                                     params={"session_id": session_id})
            
            if response.status_code == 200:
                print("Bot:", response.json()['response'])
            else:
                print(f"Error: Received status code {response.status_code}")
                print(f"Response content: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with the backend: {e}")

if __name__ == "__main__":
    chat_with_model()