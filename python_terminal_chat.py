import requests
import time
import traceback
import sys
import os

# Add the backend directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')
sys.path.append(backend_dir)

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
        
        # Send the input to the backend's /solve endpoint
        try:
            print("Sending request to backend...")
            start_time = time.time()
            response = requests.post(f"{BASE_URL}/solve", 
                                     json={"question": user_input}, 
                                     params={"session_id": session_id},
                                     timeout=120)
            end_time = time.time()
            print(f"Request took {end_time - start_time:.2f} seconds")
            
            if response.status_code == 200:
                data = response.json()
                print("Bot:", data['solution'])
                
                # Process the user's response
                user_response = input("You: ")
                process_response = requests.post(f"{BASE_URL}/process_response",
                                                 json={"response": user_response},
                                                 params={"session_id": session_id})
                if process_response.status_code == 200:
                    process_data = process_response.json()
                    if process_data['progress_made']:
                        print("Bot: Great! You're making progress. " + process_data['next_step'])
                    else:
                        print("Bot: " + process_data['next_step'])
                else:
                    print("Failed to process the response.")
                
            else:
                print(f"Error: Received status code {response.status_code}")
                print(f"Response content: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with the backend: {e}")
            print(f"Error details: {traceback.format_exc()}")

if __name__ == "__main__":
    chat_with_model()