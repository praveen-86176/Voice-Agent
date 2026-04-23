from agent.agent_core import AriAgent
from agent.system_prompt import SYSTEM_PROMPT
from agent.tool_schemas import TOOL_SCHEMAS
from voice.stt import capture_microphone_input, speech_to_text
from voice.tts import speak


def agent_loop() -> None:
    agent = AriAgent()
    while True:
        # STEP 1 — Voice Input
        try:
            audio = capture_microphone_input()
        except Exception:
            speak("I didn't quite catch that — could you repeat it?")
            continue
        user_text = speech_to_text(audio)
        if not user_text:
            # Silent retry on no speech to keep voice UX natural.
            continue

        if user_text.lower() in {"exit", "quit", "bye"}:
            speak("Talk soon.")
            break

        # STEP 2 — Inject Long-Term Memory Context
        relevant_memories = agent.recall_top_memories(user_text, top_k=3)
        memory_context = agent.format_memory_injection(relevant_memories)

        # STEP 3 — Build Message Payload
        messages = agent.build_messages(
            system_prompt=SYSTEM_PROMPT,
            memory_context=memory_context,
            user_text=user_text,
        )

        # STEP 4 — LLM Reasoning (with tool schema)
        response = agent.call_llm(messages, tools=TOOL_SCHEMAS)

        # STEP 5 — Tool Execution or Direct Reply
        if response.tool_calls:
            tool_messages = agent.execute_tool_calls(response.tool_calls)
            messages.extend(tool_messages)
            final_response = agent.call_llm(messages).content
        else:
            final_response = response.content

        # STEP 6 — Speak Response
        speak(final_response)

        # STEP 7 — Update Session Context
        agent.update_session_context(user_text, final_response)


if __name__ == "__main__":
    speak("Hi, I’m ARIA. What would you like to do today?")
    agent_loop()
