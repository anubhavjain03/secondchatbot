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
st.title("Indian Cuisine AI Nutrition Coach")
st.markdown("<style>.main-title {text-align: left; font-size: 1.5rem; font-family: 'Arial'; color: #2c3e50;}</style>", unsafe_allow_html=True)

st.subheader("Created by Anubhav Jain, Entrepreneur, Author and Master Health Coach")

# Onboarding message displayed only once
if "onboarded" not in st.session_state:
    st.session_state.onboarded = False

if not st.session_state.onboarded:
    st.info(
        "Welcome to the Indian Cuisine AI Nutrition Coach! Here's how you can interact with me:\n"
        "- Ask me questions about healthy eating based on Indian cuisine.\n"
        "- Share your dietary preferences or restrictions for personalized advice.\n"
        "- Explore balanced meal options, portion control tips, and more!\n"
        "- Participate in daily challenges to improve your nutrition habits.\n"
        "Type your question below to get started."
    )
    st.session_state.onboarded = True

# Sidebar for progress tracking and customization
st.sidebar.header("🌟 Your Progress 🌟")
st.sidebar.markdown("<style>.sidebar-title {font-family: 'Verdana'; color: #8e44ad;}</style>", unsafe_allow_html=True)
st.sidebar.write(f"**Days Active:** {st.session_state.progress['days_active']}")
st.sidebar.write(f"**Goals Achieved:** {st.session_state.progress['goals_achieved']}")
st.sidebar.write(f"**Current Streak:** {st.session_state.progress['current_streak']}")

# Button to mark daily challenge completion
if st.button("✅ Complete Today's Challenge"):
    st.session_state.progress["days_active"] += 1
    st.session_state.progress["goals_achieved"] += 1
    st.session_state.progress["current_streak"] += 1
    st.success("Great job! You've completed today's challenge.")

# Dropdown for system message templates
with st.sidebar:
    templates = [
        "You are a helpful nutrition assistant specialized in Indian cuisine.",
        "You are a friendly coach focused on sustainable and healthy eating habits.",
        "You are an evidence-based guide helping users make informed dietary decisions."
    ]
    if st.session_state.system_message not in templates:
        st.session_state.system_message = templates[0]
    st.session_state.system_message = st.selectbox(
        "🎨 Customize Bot Behavior 🎨",
        templates,
        index=templates.index(st.session_state.system_message),
        help="Choose a predefined template to customize the bot's behavior."
    )

# Quick suggestion buttons for user convenience
st.markdown("### 🍴 Quick Suggestions 🍴")
st.markdown("<style>.quick-buttons {text-align: center;}</style>", unsafe_allow_html=True)
suggestions = ["What are healthy breakfast options?", "How can I reduce sugar in my diet?", "What are good protein sources in Indian food?", "How can I balance my meals?"]
for suggestion in suggestions:
    if st.button(f"🔹 {suggestion}"):
        st.session_state.messages.append({"role": "user", "content": suggestion})

# Capture user input through chat
if prompt := st.chat_input("Your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})

# Display previous chat messages
st.markdown("<div style='background-color: #f7f9fc; padding: 10px; border-radius: 5px;'>", unsafe_allow_html=True)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
st.markdown("</div>", unsafe_allow_html=True)

# Generate a response if the last message is not from the assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Validate session state before constructing the prompt
            system_message = st.session_state.system_message if isinstance(st.session_state.system_message, str) else "Default system message."
            last_user_message = st.session_state.messages[-1]['content'] if 'content' in st.session_state.messages[-1] else "No user input provided."
            context_prompt = f"System Message: {system_message}\n{last_user_message}"
            response = conversation.predict(input=context_prompt)
            st.write(response)
            st.markdown(":star2: Great insight! Keep exploring healthy choices! :star2:")  # Add visual feedback
            message = {"role": "assistant", "content": response}
            st.session_state.messages.append(message)  # Add response to message history
