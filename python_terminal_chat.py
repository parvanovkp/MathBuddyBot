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
                
                while True:
                    action = input("Enter 'hint' for a hint, 'validate' to check your answer, or 'next' to continue: ").lower()
                    if action == 'hint':
                        hint_response = requests.post(f"{BASE_URL}/get_hint", 
                                                      json={"session_id": session_id})
                        if hint_response.status_code == 200:
                            print("Hint:", hint_response.json()['hint'])
                        else:
                            print("Failed to get a hint.")
                    elif action == 'validate':
                        answer = input("Enter your answer: ")
                        validation_response = requests.post(f"{BASE_URL}/validate_answer", 
                                                            json={"answer": answer},
                                                            params={"session_id": session_id})
                        if validation_response.status_code == 200:
                            validation_data = validation_response.json()
                            print(f"Is correct: {validation_data['is_correct']}")
                            print(f"Feedback: {validation_data['feedback']}")
                        else:
                            print("Failed to validate the answer.")
                    elif action == 'next':
                        break
                    else:
                        print("Invalid input. Please enter 'hint', 'validate', or 'next'.")
                
                progress_response = requests.get(f"{BASE_URL}/get_progress", 
                                                 params={"session_id": session_id})
                if progress_response.status_code == 200:
                    progress = progress_response.json()
                    print(f"\nCurrent progress - Topic: {progress['topic']}, Difficulty: {progress['difficulty']}")
                else:
                    print("Failed to get current progress.")
                
            else:
                print(f"Error: Received status code {response.status_code}")
                print(f"Response content: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with the backend: {e}")
            print(f"Error details: {traceback.format_exc()}")

if __name__ == "__main__":
    chat_with_model()