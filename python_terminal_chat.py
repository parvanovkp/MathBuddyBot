import requests

# Set your backend URL
BASE_URL = "http://localhost:8000"

def chat_with_model():
    print("Welcome to the DSPy Chat Terminal!")
    print("Type 'exit' to quit the chat.")
    
    while True:
        # Get user input
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        # Send the input to the backend's /solve endpoint
        response = requests.post(f"{BASE_URL}/solve", json={"question": user_input})
        
        if response.status_code == 200:
            data = response.json()
            print(f"Model: {data['summary']}")
        else:
            print("Error communicating with the model. Please try again.")

if __name__ == "__main__":
    chat_with_model()

