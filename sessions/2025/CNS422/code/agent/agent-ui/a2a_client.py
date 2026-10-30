
import asyncio
import logging
import os
from typing import Optional
from uuid import uuid4
from urllib.parse import quote
import boto3

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.types import Message, Part, Role, TextPart, Task, Artifact

from dotenv import load_dotenv
load_dotenv()  # take environment variables

#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 300  # set request timeout to 5 minutes

def get_bearer_token():
    required_vars = ['CLIENT_ID', 'AGENT_USERNAME', 'AGENT_USER_PASSWORD']

    for var in required_vars:
        if var not in os.environ:
            print(f"Error: {var} environment variable not defined")
            return None

    client = boto3.client('cognito-idp', region_name='us-west-2')

    response = client.initiate_auth(
        ClientId=os.getenv('CLIENT_ID'),
        AuthFlow='USER_PASSWORD_AUTH',
        AuthParameters={
            'USERNAME': os.getenv('AGENT_USERNAME'),
            'PASSWORD': os.getenv('AGENT_USER_PASSWORD')
        }
    )

    return response['AuthenticationResult']['AccessToken']


def create_message(*, role: Role = Role.user, text: str) -> Message:
    return Message(
        kind="message",
        role=role,
        parts=[Part(TextPart(kind="text", text=text))],
        message_id=uuid4().hex,
    )


def extract_text_from_task(task: Task) -> str:
    """Extract all text parts from task artifacts and combine into a single string."""
    text_parts = []

    if not task or not task.artifacts:
        return ""

    artifact: Artifact
    for artifact in task.artifacts:
        part: Part
        for part in artifact.parts:
            # Part is a wrapper, access the actual part content
            actual_part = part.root if hasattr(part, 'root') else part
            if hasattr(actual_part, 'kind') and actual_part.kind == "text":
                text_parts.append(actual_part.text)
            elif isinstance(actual_part, TextPart):
                text_parts.append(actual_part.text)

    return "\n".join(text_parts)

async def send_sync_message(message: str, runtime_url: str = "http://localhost:9000/", session_id: Optional[str] = None) -> tuple[Optional[Task], Optional[str]]:
    # Use provided session_id or generate a new one
    if not session_id:
        session_id = str(uuid4())
        print(f"Generated new session ID: {session_id}")
    else:
        print(f"Reusing session ID: {session_id}")

    print(f"Runtime URL: {runtime_url}")

    # Prepare headers - add Authorization only for HTTPS URLs
    headers = {'X-Amzn-Bedrock-AgentCore-Runtime-Session-Id': session_id}

    if runtime_url.startswith("https"):
        bearer_token = get_bearer_token()
        if not bearer_token:
            raise ValueError("Bearer token not found in environment variables.")
        print(f"Bearer token obtained: {bearer_token[:20]}...")
        headers["Authorization"] = f"Bearer {bearer_token}"

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, headers=headers) as httpx_client:
        # Get agent card from the runtime URL
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=runtime_url)
        try:
            agent_card = await resolver.get_agent_card()
            print(f"Agent card retrieved successfully")
            print(f"Agent card URL: {agent_card.url if hasattr(agent_card, 'url') else 'N/A'}")
        except Exception as e:
            print(f"Error getting agent card: {type(e).__name__}: {e}")
            raise

        # Agent card contains the correct URL (same as runtime_url in this case)
        # No manual override needed - this is the path-based mounting pattern

        # Create client using factory
        config = ClientConfig(
            httpx_client=httpx_client,
            streaming=False,  # Use non-streaming mode for sync response
        )
        factory = ClientFactory(config)
        client = factory.create(agent_card)

        # Create and send message
        msg = create_message(text=message)

        # With streaming=False, this will yield exactly one result
        max_retries = 2
        retry_delay = 15

        for attempt in range(max_retries + 1):
            try:
                async for event in client.send_message(msg):
                    if isinstance(event, Message):
                        logger.debug(event.model_dump_json(exclude_none=True, indent=2))
                        #return event
                    elif isinstance(event, tuple) and len(event) == 2:
                        # (Task, UpdateEvent) tuple
                        task: Task
                        task, update_event = event
                        logger.debug(f"Task: {task.model_dump_json(exclude_none=True, indent=2)}")
                        if update_event:
                            logger.debug(f"Update: {update_event.model_dump_json(exclude_none=True, indent=2)}")
                        return task, session_id
                    else:
                        # Fallback for other response types
                        logger.info(f"Response: {str(event)}")
                        #return event
                break  # Success, exit retry loop
            except Exception as e:
                if attempt < max_retries:
                    print(f"Error during send_message (attempt {attempt + 1}/{max_retries + 1}): {type(e).__name__}: {e}")
                    print(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"Error during send_message (final attempt): {type(e).__name__}: {e}")
                    logger.exception("All retry attempts failed:")
                    raise

    # If no result was returned, return None for both
    return None, session_id

def send_message(message, session_id: Optional[str] = None):
    # Usage examples:
    # 1. Default localhost: send_message("what is 101 * 11")
    # 2. With session: send_message("what is 101 * 11", session_id="existing-session-id")
    runtime_url = "http://localhost:9000/"
    # if AGENT_ARN is set then runtime_url = f"https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/{escaped_agent_arn}/invocations/"
    agent_arn = os.getenv('AGENT_ARN')
    if agent_arn:
        # URL encode the agent ARN
        escaped_agent_arn = quote(agent_arn, safe='')
        # Construct the URL
        runtime_url = f"https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/{escaped_agent_arn}/invocations/"

    task_result, returned_session_id = asyncio.run(send_sync_message(message, runtime_url, session_id))

    # Extract and print all text from task
    if task_result:
        response_text = extract_text_from_task(task_result)
        if response_text:
            print(f"\nAgent Response:\n{response_text}")
            return response_text, returned_session_id
        else:
            print("No text found in task result.")
            return "No text found in task result.", returned_session_id
    return "No response from agent.", returned_session_id

# Test the function
if __name__ == "__main__":
    PROMPT_MESSAGE = os.getenv('PROMPT_MESSAGE', "what is 101 * 11")
    send_message(PROMPT_MESSAGE)

