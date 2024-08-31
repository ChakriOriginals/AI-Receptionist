import streamlit as st
import time
import random
import threading
from datetime import datetime, timedelta

class State:
    INITIAL = 'initial'
    EMERGENCY = 'emergency'
    MESSAGE = 'message'
    LOCATION = 'location'
    APPOINTMENT = 'appointment'
    GENERAL_QUESTION = 'general_question'
    FINAL = 'final'

class AIReceptionist:
    def __init__(self):
        self.reset()

    def reset(self):
        self.state = State.INITIAL
        self.emergency_type = None
        self.location = None
        self.message = None
        self.database_thread = None
        self.emergency_responses = {
            "not breathing": [
                "Call emergency services immediately.",
                "Begin CPR if you're trained:",
                "- Place hands on the center of the chest",
                "- Push hard and fast at a rate of 100-120 compressions per minute",
                "- Allow the chest to fully recoil between compressions",
                "Continue until emergency services arrive"
            ],
            "chest pain": [
                "Call emergency services immediately.",
                "Help the person sit down and rest in a comfortable position.",
                "If the person takes nitroglycerin, help them take it.",
                "If aspirin is readily available and the person isn't allergic, have them chew a baby aspirin.",
                "Loosen any tight clothing.",
                "Stay with the person until emergency services arrive."
            ],
            "severe bleeding": [
                "Call emergency services immediately.",
                "Apply direct pressure to the wound using a clean cloth or sterile bandage.",
                "If possible, elevate the injured area above the heart.",
                "Do not remove the cloth or bandage if it becomes soaked; add more on top.",
                "If bleeding is from an arm or leg, and not controlled, apply pressure to the appropriate artery.",
                "Stay with the person until emergency services arrive."
            ],
            "broken bone": [
                "Call emergency services for serious fractures.",
                "Keep the injured area still and supported.",
                "Apply a cold pack wrapped in a cloth to reduce swelling.",
                "For an open fracture, cover the wound with a clean cloth or sterile bandage.",
                "Do not attempt to realign the bone or push a protruding bone back in.",
                "Stay with the person until emergency services arrive."
            ],
            "allergic reaction": [
                "Call emergency services if the reaction is severe.",
                "Ask if the person has an epinephrine auto-injector (like an EpiPen) and help them use it if necessary.",
                "Help the person stay calm and lie still on their back with feet elevated.",
                "Loosen tight clothing and cover them with a blanket.",
                "Watch for signs of shock.",
                "If the person is vomiting, turn them on their side to prevent choking.",
                "Stay with the person until emergency services arrive."
            ]
        }
        self.emergency_keywords = {
            "not breathing": ["not breathing", "can't breathe", "difficulty breathing", "choking"],
            "chest pain": ["chest pain", "heart attack", "cardiac arrest"],
            "severe bleeding": ["bleeding", "blood loss", "hemorrhage"],
            "broken bone": ["broken bone", "fracture", "broken arm", "broken leg"],
            "allergic reaction": ["allergic reaction", "anaphylaxis", "allergy attack"]
        }
        self.general_questions = {
            "medication": [
                "Effective medication management is crucial for optimal health outcomes.",
                "Keep all prescribed medications in one place, preferably in a pill box or organizer.",
                "Set reminders for daily doses and track your intake using apps or paper logs.",
                "Always read medication labels carefully and follow dosage instructions precisely.",
                "If you have any questions or concerns about your medication regimen, consult Dr. Adrin during your next visit."
            ],
            "emergency": [
                "In case of a medical emergency, prioritize your safety and well-being.",
                "Call emergency services immediately if you haven't already.",
                "Provide them with as much information as possible about your condition and location.",
                "Follow any instructions given by emergency responders, including staying on the line until help arrives."
            ],
            "history": [
                "If you have questions about your medical history, it's best to consult with Dr. Adrin directly.",
                "During your next appointment, bring a list of your past diagnoses, treatments, and any ongoing conditions.",
                "This information will help Dr. Adrin provide more accurate and effective care."
            ],
            "vision": [
                "Vision health is crucial for quality of life and should be monitored regularly.",
                "Schedule an eye exam with Dr. Adrin to address any specific concerns or for regular check-ups.",
                "Practice good eye care by getting enough sleep, reducing screen time, and wearing protective eyewear when necessary."
            ],
            "talks": [
                "TED Talks often feature insightful discussions on various health topics.",
                "Some popular health-related TED Talks include 'Your body language shapes who you are,' 'Grit: The power of passion and perseverance,' and 'How to spot a liar.'",
                "While these talks can be thought-provoking, always consult with healthcare professionals for personalized advice."
            ],
            "books or resources?": [
                "While I can suggest popular health-related books and resources, always verify the credibility of sources.",
                "Some recommended books include 'Why Zebras Don't Get Ulcers' by Robert Sapolsky and 'The Blue Zones' by Dan Buettner.",
                "For current and reliable health information, consult reputable websites like Mayo Clinic or the CDC."
            ]
        }

    def get_emergency_response(self, emergency_type):
        for key, keywords in self.emergency_keywords.items():
            if any(keyword in emergency_type.lower() for keyword in keywords):
                return self.emergency_responses[key]
        return ["Please stay calm and describe your emergency in more detail.",
                "If it's life-threatening, call emergency services immediately.",
                "I'll do my best to provide appropriate guidance based on the information you give me."]

    def process_appointment_request(self, date_time_str):
        try:
            requested_datetime = datetime.strptime(date_time_str, "%A %I:%M %p %B %d %Y")
            now = datetime.now()
            
            if requested_datetime < now:
                return "I'm sorry, but that date is in the past. Could you please provide a future date and time?"
            
            # Check if it's within office hours (assuming 9 AM to 5 PM, Monday to Friday)
            if requested_datetime.weekday() >= 5 or requested_datetime.hour < 9 or requested_datetime.hour >= 17:
                return "I'm sorry, but that time is outside of our office hours. We're open Monday to Friday, 9 AM to 5 PM. Could you please suggest another time?"
            
            # If all checks pass, confirm the appointment
            return f"Great! I've scheduled your appointment for {requested_datetime.strftime('%A, %B %d, %Y at %I:%M %p')}. Is there anything else you need?"
        
        except ValueError:
            return "I'm sorry, I couldn't understand that date and time. Could you please provide it in the format 'Day Time AM/PM Month Date Year'? For example, 'Friday 3:30 PM September 6 2024'."

    def process_input(self, user_input):
        user_input = user_input.strip().lower()

        # Handle greetings
        greetings = ["hi", "hello", "hey", "greetings"]
        if any(greeting in user_input for greeting in greetings):
            self.reset()
            return "Hello! How can I assist you today? Are you having an emergency, would you like to leave a message, schedule an appointment, or do you have a general medical question?"

        # Handle thanks
        thanks = ["thank you", "thanks", "appreciate it", "ok"]
        if any(thank in user_input for thank in thanks):
            return "Great! Is there anything else I can help you with?"

        # Handle apologies
        apologies = ["sorry", "apologies", "my bad"]
        if any(apology in user_input for apology in apologies):
            return "No need to apologize. How can I assist you today?"

        if self.state == State.INITIAL:
            if "emergency" in user_input:
                self.state = State.EMERGENCY
                return "I understand this is an emergency. Can you please tell me what the specific emergency is?"
            elif "message" in user_input:
                self.state = State.MESSAGE
                return "Certainly, I can take a message for Dr. Adrin. What message would you like to leave?"
            elif "appointment" in user_input:
                self.state = State.APPOINTMENT
                return "I'd be happy to help you schedule an appointment. Please provide the date and time you'd like, in the format 'Day Time AM/PM Month Date Year'. For example, 'Friday 3:30 PM September 6 2024'."
            elif any(keyword in user_input for keyword in self.general_questions.keys()):
                self.state = State.GENERAL_QUESTION
                return self.handle_general_question(user_input)
            else:
                return "I'm sorry, I didn't understand that. Are you having an emergency, would you like to leave a message, schedule an appointment, or do you have a general medical question?"

        elif self.state == State.EMERGENCY:
            self.emergency_type = user_input
            emergency_response = self.get_emergency_response(self.emergency_type)
            self.state = State.FINAL
            return "I understand you're experiencing " + self.emergency_type + ". Here's what you should do:\n\n" + "\n".join(emergency_response) + "\n\nIs there anything else I can help you with?"

        elif self.state == State.MESSAGE:
            self.message = user_input
            self.state = State.FINAL
            return "Thanks for the message. We will forward it to Dr. Adrin. Is there anything else I can help you with?"

        elif self.state == State.APPOINTMENT:
            response = self.process_appointment_request(user_input)
            self.state = State.FINAL
            return response

        elif self.state == State.GENERAL_QUESTION:
            response = self.handle_general_question(user_input)
            self.state = State.FINAL
            return response + "\n\nIs there anything else I can help you with?"

        elif self.state == State.FINAL:
            if "appointment" in user_input:
                self.state = State.APPOINTMENT
                return "Certainly! I'd be happy to help you schedule an appointment. Please provide the date and time you'd like, in the format 'Day Time AM/PM Month Date Year'. For example, 'Friday 3:30 PM September 6 2024'."
            elif "emergency" in user_input:
                self.state = State.EMERGENCY
                return "I understand this is an emergency. Can you please tell me what the specific emergency is?"
            elif "message" in user_input:
                self.state = State.MESSAGE
                return "Of course, I can take a message for Dr. Adrin. What message would you like to leave?"
            elif any(keyword in user_input for keyword in self.general_questions.keys()):
                self.state = State.GENERAL_QUESTION
                return self.handle_general_question(user_input)
            elif "yes" in user_input or "another" in user_input:
                self.reset()
                return "How else can I assist you today? Do you need emergency help, want to leave a message, schedule an appointment, or have a general medical question?"
            else:
                self.reset()
                return "Is there anything else I can help you with? If not, please don't hesitate to reach out if you need further assistance."

        return "I'm sorry, I don't understand that. Could you please rephrase your request?"

    def handle_general_question(self, user_input):
        for keyword, response in self.general_questions.items():
            if keyword in user_input:
                return "\n".join(response)
        return "I'm sorry, I couldn't find specific information about that. It's best to discuss this with Dr. Adrin during your next appointment. Is there anything else I can help you with?"

def main():
    st.title("Dr. Adrin's AI Receptionist")

    # Initialize session state
    if 'ai_receptionist' not in st.session_state:
        st.session_state.ai_receptionist = AIReceptionist()

    # Display chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("You:"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        response = st.session_state.ai_receptionist.process_input(prompt)

        # Add AI response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

    # Reset button
    if st.button("Start Over"):
        st.session_state.ai_receptionist = AIReceptionist()
        st.session_state.messages = []
        st.experimental_rerun()

if __name__ == "__main__":
    main()