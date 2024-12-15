import streamlit as st
from streamlit_chat import message
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory

import os

# Initialize session state variables for memory
if 'buffer_memory' not in st.session_state:
    st.session_state.buffer_memory = ConversationBufferWindowMemory(k=4, return_messages=True)

# Initialize the chat message history
if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help you eat healthier today?"}
    ]

# Initialize the system message with default behavior
if "system_message" not in st.session_state:
    st.session_state.system_message = (
        "You are a helpful nutrition assistant specialized in providing evidence-based dietary advice with a focus on Indian cuisine. Your goal is to help users make healthier choices by considering their cultural preferences, local ingredients, and scientific nutritional principles. Provide detailed but clear explanations and practical advice tailored to Indian meal patterns, festivals, and traditional cooking methods. Emphasize balanced nutrition, portion control, and sustainable habits. Avoid recommending extreme diets or unproven trends."
    )

# Initialize progress tracking metrics
if "progress" not in st.session_state:
    st.session_state.progress = {"days_active": 0, "goals_achieved": 0, "current_streak": 0}

# Initialize ChatOpenAI and ConversationChain
llm = ChatOpenAI(
    model="meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
    openai_api_key=st.secrets["TOGETHER_API_KEY"],  # Access API key from secrets
    openai_api_base="https://api.together.xyz/v1"  # Specify API base URL
)

# Error handling for ConversationChain initialization
try:
    conversation = ConversationChain(memory=st.session_state.buffer_memory, llm=llm)
except Exception as e:
    st.error(f"Failed to initialize the conversation chain: {e}")
    st.stop()

# User Interface setup
st.title("🗣️ Conversational Chatbot")
st.subheader("A Simple Chat Interface for Nutrition Guidance")

# Sidebar for customization and progress tracking
st.sidebar.header("Customize and Track Progress")

# Dropdown for system message templates
templates = [
    "You are a helpful nutrition assistant specialized in Indian cuisine.",
    "You are a friendly coach focused on sustainable and healthy eating habits.",
    "You are an evidence-based guide helping users make informed dietary decisions."
]
if st.session_state.system_message not in templates:
    st.session_state.system_message = templates[0]
st.session_state.system_message = st.sidebar.selectbox(
    "System Message Templates",
    templates,
    index=templates.index(st.session_state.system_message),
    help="Choose a predefined template to customize the bot's behavior."
)

# Display progress tracking in the sidebar
st.sidebar.write(f"**Days Active:** {st.session_state.progress['days_active']}")
st.sidebar.write(f"**Goals Achieved:** {st.session_state.progress['goals_achieved']}")
st.sidebar.write(f"**Current Streak:** {st.session_state.progress['current_streak']}")

# Button to mark daily challenge completion
if st.sidebar.button("Complete Today's Challenge"):
    st.session_state.progress["days_active"] += 1
    st.session_state.progress["goals_achieved"] += 1
    st.session_state.progress["current_streak"] += 1
    st.sidebar.success("Great job! You've completed today's challenge.")

# Input prompt for user
prompt = st.text_input("Your question:", placeholder="Type your question here")

# Display prior chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        st.write(f"🧑 {message['content']}")
    else:
        st.write(f"🤖 {message['content']}")

# Generate response if user input is provided
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Thinking..."):
        try:
            system_message = st.session_state.system_message
            context_prompt = f"System Message: {system_message}\n{prompt}"
            response = conversation.predict(input=context_prompt)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.write(f"🤖 {response}")
        except Exception as e:
            st.error(f"Error generating response: {e}")
