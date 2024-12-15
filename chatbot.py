import streamlit as st
from streamlit_chat import message
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory

import os

# Initialize session state variables
if 'buffer_memory' not in st.session_state:
    st.session_state.buffer_memory = ConversationBufferWindowMemory(k=3, return_messages=True)

if "messages" not in st.session_state.keys(): # Initialize the chat message history
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help you eat healthier today?"}
    ]

if "system_message" not in st.session_state: # Initialize system message
    st.session_state.system_message = (
        "You are a helpful nutrition assistant specialized in providing evidence-based dietary advice with a focus on Indian cuisine. Your goal is to help users make healthier choices by considering their cultural preferences, local ingredients, and scientific nutritional principles. Provide detailed but clear explanations and practical advice tailored to Indian meal patterns, festivals, and traditional cooking methods. Emphasize balanced nutrition, portion control, and sustainable habits. Avoid recommending extreme diets or unproven trends."
    )

# Initialize ChatOpenAI and ConversationChain
llm = ChatOpenAI(
    model = "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
    openai_api_key = st.secrets["TOGETHER_API_KEY"],  # use your key
    openai_api_base = "https://api.together.xyz/v1"
)

conversation = ConversationChain(memory=st.session_state.buffer_memory, llm=llm)

# Create user interface
st.title("🗣️ Conversational Chatbot")
st.subheader("⑫ Simple Chat Interface for LLMs by Build Fast with AI")

# Allow customization of system message
with st.sidebar:
    st.text_input("System Message", key="system_message", help="Customize the system's behavior.")

if prompt := st.chat_input("Your question"): # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Add the system message to the context before generating a response
            context_prompt = f"System Message: {st.session_state.system_message}\n" + prompt
            response = conversation.predict(input=context_prompt)
            st.write(response)
            message = {"role": "assistant", "content": response}
            st.session_state.messages.append(message) # Add response to message history
