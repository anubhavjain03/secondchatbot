import streamlit as st
from streamlit_chat import message
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory

import os

# Initialize session state variables
if 'buffer_memory' not in st.session_state:
    st.session_state.buffer_memory = ConversationBufferWindowMemory(k=4, return_messages=True)

if "messages" not in st.session_state.keys(): # Initialize the chat message history
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help you eat healthier today?"}
    ]

if "system_message" not in st.session_state: # Initialize system message
    st.session_state.system_message = (
        "You are a helpful nutrition assistant specialized in providing evidence-based dietary advice with a focus on Indian cuisine. Your goal is to help users make healthier choices by considering their cultural preferences, local ingredients, and scientific nutritional principles. Provide detailed but clear explanations and practical advice tailored to Indian meal patterns, festivals, and traditional cooking methods. Emphasize balanced nutrition, portion control, and sustainable habits. Avoid recommending extreme diets or unproven trends."
    )

if "progress" not in st.session_state: # Initialize progress tracking
    st.session_state.progress = {"days_active": 0, "goals_achieved": 0, "current_streak": 0}

# Initialize ChatOpenAI and ConversationChain
llm = ChatOpenAI(
    model = "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
    openai_api_key = st.secrets["TOGETHER_API_KEY"],  # use your key
    openai_api_base = "https://api.together.xyz/v1"
)

conversation = ConversationChain(memory=st.session_state.buffer_memory, llm=llm)

# Create user interface
st.title("Indian Cuisine AI Nutrition Coach")
st.subheader("Created by Anubhav Jain, Entrepreneur, Author and Master Health Coach")

# Add onboarding message
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

# Progress tracking and challenges
st.sidebar.header("Your Progress")
st.sidebar.write(f"Days Active: {st.session_state.progress['days_active']}")
st.sidebar.write(f"Goals Achieved: {st.session_state.progress['goals_achieved']}")
st.sidebar.write(f"Current Streak: {st.session_state.progress['current_streak']}")

if st.button("Complete Today's Challenge"):
    st.session_state.progress["days_active"] += 1
    st.session_state.progress["goals_achieved"] += 1
    st.session_state.progress["current_streak"] += 1
    st.success("Great job! You've completed today's challenge.")

# Allow customization of system message
with st.sidebar:
    st.selectbox(
        "System Message Templates",
        [
            "You are a helpful nutrition assistant specialized in Indian cuisine.",
            "You are a friendly coach focused on sustainable and healthy eating habits.",
            "You are an evidence-based guide helping users make informed dietary decisions."
        ],
        key="system_message",
        help="Choose a predefined template to customize the bot's behavior."
    )

# Add quick suggestion buttons
st.markdown("### Quick Suggestions")
suggestions = ["What are healthy breakfast options?", "How can I reduce sugar in my diet?", "What are good protein sources in Indian food?", "How can I balance my meals?"]
for suggestion in suggestions:
    if st.button(suggestion):
        st.session_state.messages.append({"role": "user", "content": suggestion})

if prompt := st.chat_input("Your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Add the system message to the context before generating a response
            context_prompt = f"System Message: {st.session_state.system_message}\n" + st.session_state.messages[-1]["content"]
            response = conversation.predict(input=context_prompt)
            st.write(response)
            st.markdown(":star2: Great insight! Keep exploring healthy choices! :star2:")  # Add visual feedback
            message = {"role": "assistant", "content": response}
            st.session_state.messages.append(message) # Add response to message history
