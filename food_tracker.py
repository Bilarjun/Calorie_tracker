import firebase_admin
from firebase_admin import credentials, firestore, auth
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Firebase initialization
if not firebase_admin._apps:
    cred = credentials.Certificate(
        r"foodtracker-79ec9-firebase-adminsdk-10wl9-af1a707ca6.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


# Function to fetch calories from Nutritionix API
def fetch_calories_from_nutritionix(food_item, quantity):
    API_URL = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    API_KEY = "01cdcf515d8e7813ca086b9a1c673891"
    APP_ID = "5ed53420"
    headers = {
        "x-app-id": APP_ID,
        "x-app-key": API_KEY,
    }
    data = {
        "query": food_item
    }
    response = requests.post(API_URL, headers=headers, json=data)
    if response.status_code == 200:
        nutrients = response.json()["foods"][0]
        calories_per_unit = nutrients["nf_calories"]
        total_calories = calories_per_unit * quantity
        return total_calories
    else:
        st.error("Failed to fetch data from Nutritionix API")
        return None


# Function to save data to Firebase
def save_log_to_firebase(log, user_id):
    db.collection("users").document(user_id).collection("food_logs").add(log)


# Function for user authentication
def user_authentication():
    st.header("User Authentication")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Sign In"):
        try:
            user_query = db.collection("users").where("email", "==", email).get()
            if not user_query:
                st.error("User not found. Please check your credentials or sign up.")
            else:
                user_data = user_query[0].to_dict()
                if user_data["password"] == password:
                    st.success(f"Welcome back, {email}!")
                    user_id = user_query[0].id
                    st.session_state.user_id = user_id
                    st.session_state.page = "main"
                    st.experimental_rerun()
                else:
                    st.error("Incorrect password. Please try again.")
        except Exception as e:
            st.error(f"Error during sign-in: {e}")


# Function for user signup
def user_signup():
    st.header("User Signup")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    age = st.number_input("Age", min_value=0, max_value=150, value=0)
    height = st.number_input("Height (cm)", min_value=0.0, value=0.0)
    weight = st.number_input("Weight (kg)", min_value=0.0, value=0.0)
    gender = st.radio("Gender", ("Male", "Female", "Other"))
    weight_goal = st.selectbox("Weight Goal", ["Lose Weight", "Maintain Weight", "Gain Weight"])

    if st.button("Next"):
        user_query = db.collection("users").where("email", "==", email).get()
        if user_query:
            st.error("User already exists. Please sign in.")
        else:
            st.session_state.signup_data = {
                "email": email,
                "password": password,
                "age": age,
                "height": height,
                "weight": weight,
                "gender": gender,
                "weight_goal": weight_goal
            }
            st.session_state.signup_step = "terms"


# Terms and conditions popup
def terms_and_conditions():
    st.header("Terms and Conditions")
    st.write("""
    **Terms and Conditions**

    **Last Updated: May 31, 2024**

    Welcome to Calorie Tracker! These terms and conditions outline the rules and regulations for the use of our application.

    **1. Acceptance of Terms**

    By accessing and using Calorie Tracker, you accept and agree to be bound by the terms and conditions of this agreement. If you do not agree to these terms, you should not use the app.

    **2. User Accounts**

    - You must create an account to use certain features of the app. You are responsible for maintaining the confidentiality of your account information and for all activities that occur under your account.
    - You agree to provide accurate and complete information when creating your account and to update your information as necessary.

    **3. Privacy**

    - Your use of the app is also governed by our Privacy Policy, which is incorporated into these terms by this reference. Please review our Privacy Policy to understand our practices regarding the collection, use, and disclosure of your personal information.

    **4. Use of the App**

    - You agree to use the app only for lawful purposes and in accordance with these terms.
    - You agree not to use the app in any way that could damage, disable, overburden, or impair the app or interfere with any other party’s use of the app.

    **5. Content**

    - The app allows you to log food items and track calorie intake. You are solely responsible for the accuracy of the information you provide.
    - We do not warrant the accuracy, completeness, or usefulness of the information provided by the Nutritionix API or any other data source.

    **6. Intellectual Property**

    - The app and its original content, features, and functionality are and will remain the exclusive property of Calorie Tracker and its licensors.
    - You may not modify, distribute, transmit, display, perform, reproduce, publish, license, create derivative works from, transfer, or sell any information or services obtained from the app.

    **7. Termination**

    - We may terminate or suspend your account and bar access to the app immediately, without prior notice or liability, under our sole discretion, for any reason whatsoever and without limitation, including but not limited to a breach of these terms.
    - If you wish to terminate your account, you may simply discontinue using the app.

    **8. Limitation of Liability**

    - In no event shall Calorie Tracker, nor its directors, employees, partners, agents, suppliers, or affiliates, be liable for any indirect, incidental, special, consequential, or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses, resulting from (i) your use or inability to use the app; (ii) any unauthorized access to or use of our servers and/or any personal information stored therein.

    **9. Changes to Terms**

    - We reserve the right, at our sole discretion, to modify or replace these terms at any time. If a revision is material, we will provide at least 30 days' notice prior to any new terms taking effect. What constitutes a material change will be determined at our sole discretion.

    **10. Governing Law**

    - These terms shall be governed and construed in accordance with the laws of [Your Country/State], without regard to its conflict of law provisions.

    **11. Contact Us**

    - If you have any questions about these terms, please contact us at arjunbilupati3051@gmail.com.

    By using the Calorie Tracker app, you acknowledge that you have read, understood, and agree to be bound by these terms and conditions.
    """)

    agree = st.radio("Do you agree to the terms and conditions?", ("No", "Yes"))
    if agree == "Yes":
        if st.button("Next"):
            st.session_state.signup_step = "complete_signup"


def complete_signup():
    signup_data = st.session_state.signup_data
    try:
        user = auth.create_user(email=signup_data["email"], password=signup_data["password"])
        st.success(f"User created: {user.email}")
        st.session_state.user_id = user.uid
        db.collection("users").document(user.uid).set(signup_data)
        st.session_state.page = "main"
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Error during sign-up: {e}")


# Calculate BMI
def calculate_bmi(weight, height):
    if height is None or weight is None or height == 0:
        return None
    bmi = weight / ((height / 100) ** 2)
    return bmi


# Function to calculate progress towards daily goal
def calculate_progress(food_log_df, daily_calories):
    if not food_log_df.empty:
        total_calories = food_log_df["Calories"].sum()
        progress_percentage = min(total_calories / daily_calories, 1.0)
    else:
        progress_percentage = 0.0
    return progress_percentage


# Function to calculate daily calorie intake based on weight goal
def calculate_daily_calories(weight, height, age, gender, weight_goal):
    # Calculate BMR (Basal Metabolic Rate) using Harris-Benedict Equation
    if gender == "Male":
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)

    # Adjust BMR based on weight goal
    if weight_goal == "Lose Weight":
        daily_calories = bmr - 250  # Subtract 250 calories for weight loss
    elif weight_goal == "Gain Weight":
        daily_calories = bmr + 250  # Add 250 calories for weight gain
    else:
        daily_calories = bmr  # Maintain weight

    return daily_calories


# Profile Editing Page
def edit_profile(user_id):
    st.header("Edit Profile")

    user_data = db.collection("users").document(user_id).get().to_dict()

    if user_data:
        email = user_data.get("email")
        age = st.number_input("Age", min_value=0, max_value=150, value=user_data.get("age", 0))
        height = st.number_input("Height (cm)", min_value=0.0, value=user_data.get("height", 0.0))
        weight = st.number_input("Weight (kg)", min_value=0.0, value=user_data.get("weight", 0.0))
        gender = st.radio("Gender", ["Male", "Female", "Other"],
                          index=["Male", "Female", "Other"].index(user_data.get("gender", "Male")))
        weight_goal = st.selectbox("Weight Goal", ["Lose Weight", "Maintain Weight", "Gain Weight"],
                                   index=["Lose Weight", "Maintain Weight", "Gain Weight"].index(
                                       user_data.get("weight_goal", "Maintain Weight")))

        # Add back button
        if st.button("Update Profile"):
            updated_data = {
                "email": email,
                "age": age,
                "height": height,
                "weight": weight,
                "gender": gender,
                "weight_goal": weight_goal
            }
            db.collection("users").document(user_id).set(updated_data)
            st.success("Profile updated successfully!")
            st.experimental_rerun()

        # Add the back button with the logic to return to the previous page
        if st.button("Back"):
            st.session_state.page = "main"
            st.experimental_rerun()


# Main Streamlit app
# Main Streamlit app
def main():
    st.sidebar.image("https://cdn.discordapp.com/attachments/1155361377981055077/1246869392810184744/image.png?ex=665df51c&is=665ca39c&hm=a60a50813d7896980761541bfcf20a37bdfbb8075950e1bd2c706d40d81228eb&",
                     use_column_width=True)
    st.sidebar.title("Calorie Tracker")

    if "signup_step" not in st.session_state:
        st.session_state.signup_step = "form"

    if "user_id" not in st.session_state:
        page = st.sidebar.radio("Are you a new user or an existing user?", ("New User", "Existing User"))
        if page == "New User":
            if st.session_state.signup_step == "form":
                user_signup()
            elif st.session_state.signup_step == "terms":
                terms_and_conditions()
            elif st.session_state.signup_step == "complete_signup":
                complete_signup()
        elif page == "Existing User":
            user_authentication()
    else:
        st.sidebar.success("Logged in successfully!")

        # Add a profile link in the sidebar
        if st.sidebar.button("View Profile"):
            st.session_state.page = "profile"
            st.experimental_rerun()

        if st.session_state.page == "profile":
            edit_profile(st.session_state.user_id)
        else:
            st.title("Calorie Tracker")

            user_id = st.session_state.user_id

            # Fetch user data
            user_data = db.collection("users").document(user_id).get().to_dict()

            # Calculate BMI
            height = user_data.get("height")
            weight = user_data.get("weight")
            if height is not None and weight is not None:
                bmi = calculate_bmi(weight, height)
                if bmi is not None:
                    st.write(f"Your BMI: {bmi:.2f}")
                else:
                    st.write("BMI cannot be calculated with the given data.")
            else:
                st.write("Height and/or weight data is missing.")

            # Goal setting
            st.header("Daily Goal")
            weight_goal = user_data.get("weight_goal", "Maintain Weight")
            st.write(f"Your weight goal: {weight_goal}")

            # Calculate suggested daily calorie intake based on weight goal
            age = user_data.get("age")
            gender = user_data.get("gender")
            if height is not None and weight is not None and age is not None and gender is not None:
                daily_calories = calculate_daily_calories(weight, height, age, gender, weight_goal)
                st.write(f"Suggested daily calorie intake: {int(daily_calories)} calories")
            else:
                st.write("Incomplete user data for calculating daily calories.")

            # Display Daily Goal and initial progress
            if "daily_calories" in locals():
                daily_goal = daily_calories
            else:
                daily_goal = 0

            # Display food logs
            food_logs = db.collection("users").document(user_id).collection("food_logs").stream()
            logs = [{"Date": log.to_dict()["Date"], "Food": log.to_dict()["Food"],
                     "Calories": log.to_dict()["Calories"]}
                    for log in food_logs]
            food_log_df = pd.DataFrame(logs)

            progress_percentage = calculate_progress(food_log_df, daily_goal)
            st.write(f"Progress: {progress_percentage:.2%}")
            st.progress(progress_percentage)

            # Display congratulatory message when 100% goal is reached
            if progress_percentage == 1.0:
                st.success("Congratulations! Your calorie goal has been completed successfully.")
                st.error("It is recommended not to consume any more calories.")

            # Add new food log
            st.header("Add a new food log")
            food = st.text_input("Food")
            quantity = st.number_input("Quantity", min_value=1, value=1)
            if st.button("Add Log"):
                if food:
                    calories = fetch_calories_from_nutritionix(food, quantity)
                    if calories is not None:
                        new_log = {"Date": datetime.today().strftime('%Y-%m-%d %H:%M:%S'), "Food": food,
                                   "Calories": calories}
                        save_log_to_firebase(new_log, user_id)
                        st.success(f"Log added: {food} - {calories} calories")
                        # Refresh the page to reflect changes
                        st.experimental_rerun()
                else:
                    st.error("Please enter a food item")

            # Display food logs
            st.header("Food Logs")
            if not food_log_df.empty:
                st.dataframe(food_log_df)
                # Display food logs

                if not food_log_df.empty:


                    # Dropdown to select logs for deletion
                    selected_log = st.selectbox("Select log to delete:",
                                                food_log_df.apply(lambda x: f"{x.name}: {x['Food']}", axis=1).tolist())

                    # Button to delete selected log
                    if st.button("Delete Log"):
                        log_index = int(selected_log.split(":")[0])
                        log_to_delete = food_log_df.iloc[log_index]["Date"]

                        # Query the log document to delete
                        log_query = db.collection("users").document(user_id).collection("food_logs").where("Date", "==",
                                                                                                           log_to_delete).limit(
                            1).get()

                        # Delete the log document
                        for log in log_query:
                            log.reference.delete()

                        st.success(f"Log {selected_log} deleted successfully!")
                        # Refresh the page to reflect changes
                        st.experimental_rerun()
                else:
                    st.write("No logs available")

                # Plotting
                st.header("Calorie Intake")
                st.line_chart(food_log_df.set_index("Date")["Calories"])
            else:
                st.write("No logs available")

        # Logout button at the bottom of the sidebar
        # Logout button at the bottom of the sidebar
        # Feedback section
        st.sidebar.subheader("Feedback")
        feedback = st.sidebar.text_area("Let us know how we can improve:", height=150)
        if st.sidebar.button("Submit Feedback"):
            # Handle feedback submission (you can implement the logic here)
            st.sidebar.success("Thank you for your feedback!")
        st.sidebar.markdown("---")
        if st.sidebar.button("⛔ Logout", key="logout_button"):
            del st.session_state["user_id"]
            st.session_state.page = "auth"  # Set page to "auth" after logout
            st.experimental_rerun()


if __name__ == "__main__":
    main()
