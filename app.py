import streamlit as st
import script

def process_string(input_string):
    # Process the input string (example: convert to uppercase)
    processed_string = input_string.upper()
    return processed_string

def main():
    st.title("appointment-booking bot string processor")
    
    # Input text box for the user to enter a string
    input_text = st.text_input("Enter a string:", "")

    # Process button to trigger string processing
    if st.button("Process"):
        # Process the input string when the button is clicked
        processed_text = script.classifyText(input_text)
        st.success(f"Processed Data: {processed_text}")

if __name__ == "__main__":
    main()