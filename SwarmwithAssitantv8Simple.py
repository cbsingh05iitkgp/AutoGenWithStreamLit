import asyncio
import streamlit as st
#from typing import Any, Dict, List
from autogen_agentchat.agents import AssistantAgent 
from autogen_agentchat.conditions import HandoffTermination, TextMentionTermination
from autogen_agentchat.messages import HandoffMessage
from autogen_agentchat.teams import Swarm 
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient




import os;
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

model_client = OpenAIChatCompletionClient(
    model="gpt-4o-mini", api_key=OPENAI_API_KEY
)
        



Assistant = AssistantAgent(
    "Assistant",
    model_client=model_client,
    handoffs=[ "user"],
    tools=[],
    description="Agent to provide answer to any question from user",
    system_message=" Answer the question and always ask user how can it help more . After sending message hand off to user",
)

termination = HandoffTermination(target="user") | TextMentionTermination("TERMINATE")
team = Swarm([Assistant], termination_condition=termination,max_turns=10)


# Streamlit UI
def main():
    st.title("Chat System")

    if "messages" not in st.session_state:
        st.session_state.messages = []
        #st.session_state.last_message = None
        st.session_state.messages.append({"role": "assistant", "content": "How can I help you?"})
        #user_input=None;

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    user_input = st.chat_input("Enter your message:")
    if user_input:
        # Append user input to messages
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        async def handle_message():
            # Create a task to send user input to the "team"
            task = HandoffMessage(
                source="user",
                target="Assistant",
                content=user_input
            )
            task_result = await team.run(task=task)
            # Get the last TextMessage
            last_message = next(
                (msg.content for msg in reversed(task_result.messages) if msg.type == "TextMessage"),
                None
            )

            # Append system response to messages
            st.session_state.messages.append({"role": "assistant", "content": last_message})
            #st.session_state.last_message = last_message

            with st.chat_message("assistant"):
                st.write(last_message)

        asyncio.run(handle_message())


if __name__ == "__main__":
    main()