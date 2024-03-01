import streamlit as st
import httpx

def authentication_form():
    # Creating form for user input
    with st.form("my_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        # Every form must have a submit button.
        submitted = st.form_submit_button("Login")
        if submitted:
            # Here you would add your authentication logic
            # For demonstration, we'll just display the input data
            st.write("You entered:")
            st.write(f"Email: {email}")
            st.write(f"Password: {password}")

            # Example of how you might handle authentication (pseudo-code)
            is_authenticated = authenticate_user(email, password)
            print(is_authenticated)
            if is_authenticated:
                st.success("You are successfully logged in.")
            else:
                st.error("Login failed. Please check your credentials.")


def login():
    st.title("Login Page")

    


def authenticate_user(email: str, password: str) -> bool:
    api_key = "AIzaSyBUgt_Of8kAw0uwsL6dpllaL077dlh74N4"
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = httpx.post(url, json=payload)
    response.raise_for_status()
    return response.json()  # This contains the ID token and other auth details

if __name__ == "__main__":
    login()
