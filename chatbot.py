import streamlit as st
from streamlit_chat import message
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
import os
import time

# Initialize session state variables for memory
if 'buffer_memory' not in st.session_state:
    st.session_state.buffer_memory = ConversationBufferWindowMemory(k=4, return_messages=True)

# Initialize the chat message history
if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help you eat healthier today?"}
    ]

# Initialize the system message with default behavior
st.session_state.system_message = st.session_state.get("system_message", 
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

# Apple-inspired minimalistic UI setup
st.markdown("""
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f8f8f8;
            margin: 0;
            padding: 0;
        }
        .main-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background: #ffffff;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .title {
            text-align: center;
            font-size: 24px;
            color: #333;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            font-size: 16px;
            color: #666;
            margin-bottom: 20px;
        }
        .sidebar {
            color: #2c3e50;
        }
        .button {
            background-color: #007aff;
            border: none;
            color: white;
            text-align: center;
            display: inline-block;
            font-size: 14px;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
        }
        .button:hover {
            background-color: #005fbc;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-container">', unsafe_allow_html=True)

# Main Title and Subtitle
st.markdown('<div class="title">Indian Cuisine AI Nutrition Coach</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your Personalized Nutrition Assistant</div>', unsafe_allow_html=True)

# Input for user prompt
prompt = st.text_input("Ask me anything about nutrition:", placeholder="e.g., What are healthy breakfast options?")

# Quick suggestions
st.markdown("<div style='margin-top: 20px;'>", unsafe_allow_html=True)
st.markdown("<strong>Quick Suggestions:</strong>", unsafe_allow_html=True)
suggestions = ["Healthy breakfast options", "How to reduce sugar in my diet", "Protein sources in Indian food", "How to balance meals"]
for suggestion in suggestions:
    if st.button(f"🔹 {suggestion}", key=suggestion):
        st.session_state.messages.append({"role": "user", "content": suggestion})
st.markdown("</div>", unsafe_allow_html=True)

# Display chat history
st.markdown("<div style='margin-top: 20px;'>", unsafe_allow_html=True)
st.markdown("<strong>Chat History:</strong>", unsafe_allow_html=True)
for message in st.session_state.messages:
    role_style = "color: #007aff;" if message["role"] == "user" else "color: #333;"
    st.markdown(f"<div style='{role_style}'>{message['content']}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Generate response for user input
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    try:
        system_message = st.session_state.system_message
        context_prompt = f"System Message: {system_message}\n{prompt}"
        max_retries = 3
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                response = conversation.predict(input=context_prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.markdown(f"<div style='color: #333;'>{response}</div>", unsafe_allow_html=True)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise e
    except Exception as e:
        st.error(f"Error generating response: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# Sidebar for customization
st.sidebar.header("Settings")
st.sidebar.markdown("<div class='sidebar'>Customize your assistant's behavior and track your progress.</div>", unsafe_allow_html=True)
st.sidebar.write(f"**Days Active:** {st.session_state.progress['days_active']}")
st.sidebar.write(f"**Goals Achieved:** {st.session_state.progress['goals_achieved']}")
st.sidebar.write(f"**Current Streak:** {st.session_state.progress['current_streak']}")

# Dropdown for system message templates
templates = [
    "You are a helpful nutrition assistant specialized in Indian cuisine.",
    "You are a friendly coach focused on sustainable and healthy eating habits.",
    "You are an evidence-based guide helping users make informed dietary decisions."
]
st.session_state.system_message = st.sidebar.selectbox(
    "Assistant Behavior:",
    templates,
    index=templates.index(st.session_state.system_message) if st.session_state.system_message in templates else 0,
    help="Select how the assistant should respond."
)
