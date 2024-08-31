import requests
import time
import traceback

# Set your backend URL
BASE_URL = "http://127.0.0.1:8000"  # Updated to match Uvicorn's default

def chat_with_model():
    print("Welcome to the Math Buddy Bot Terminal!")
    print("Type 'exit' to quit the chat.")
    
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
            response = requests.post(f"{BASE_URL}/solve", json={"question": user_input}, timeout=60)
            end_time = time.time()
            print(f"Request took {end_time - start_time:.2f} seconds")
            print(f"Received response with status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("Solution:")
                print(data['solution'])
            else:
                print(f"Error: Received status code {response.status_code}")
                print(f"Response content: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with the backend: {e}")
            print(f"Error details: {traceback.format_exc()}")

if __name__ == "__main__":
    chat_with_model()