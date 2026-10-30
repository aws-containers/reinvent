import os
from fastapi import FastAPI, Request, HTTPException
import dotenv
import uvicorn
import gradio as gr
import httpx
import logging
from urllib.parse import quote
import asyncio

import a2a_client

from dotenv import load_dotenv
load_dotenv()  # take environment variables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


user_avatar = "https://cdn-icons-png.flaticon.com/512/149/149071.png"
bot_avatar = "https://cdn-icons-png.flaticon.com/512/4712/4712042.png"

# Store session_id per Gradio session
session_store = {}

def send_message(message, session_id=None):
    response_text = a2a_client.send_message(message, session_id=session_id)
    return response_text

def chat(message, history, request: gr.Request):
    # Get or create session_id for this Gradio session
    gradio_session_id = request.session_hash

    if gradio_session_id not in session_store:
        # First message - no session_id yet, will be created by AgentCore
        session_store[gradio_session_id] = None
        logger.info(f"New Gradio session: {gradio_session_id}")

    # prepend to message the following text "Customer ID: CUST001"
    message = "My name is Emily Rodriguez with Customer ID: CUST003\n" + message

    # Send message with existing session_id (or None for first message)
    agentcore_session_id = session_store[gradio_session_id]
    response_text, returned_session_id = send_message(message, session_id=agentcore_session_id)

    # Store the session_id returned by AgentCore for subsequent requests
    if returned_session_id:
        session_store[gradio_session_id] = returned_session_id
        logger.info(f"AgentCore session_id: {returned_session_id}")

    return response_text

def on_gradio_app_load(request: gr.Request):
    return [gr.ChatMessage(
        role="assistant",
        content=f"Hi Emily Rodriguez, I'm your friendly home insurance agent! I'm here to help you with home appliances problems, like creating a claim or check on your appointments. Tell me how I can help. "
    )]

with gr.Blocks() as gradio_app:
    header = gr.Markdown("Welcome to AcmeCorp Home Insurance")

    chat = gr.ChatInterface(
        fn=chat,
        type="messages",
        chatbot=gr.Chatbot(
            type="messages",
            label="Get help for your home appliances quickly",
            avatar_images=(user_avatar, bot_avatar),
            placeholder="<b>Welcome to the AcmeCorp Home Insurance.</b>",
            height=600
        )
    )

    gradio_app.load(on_gradio_app_load, inputs=None, outputs=[chat.chatbot])

fastapi_app = FastAPI()

gr.mount_gradio_app(fastapi_app, gradio_app, path="/")

def main():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
