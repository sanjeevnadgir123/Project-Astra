import os
from groq import Groq
import logging

logger = logging.getLogger("ASTRA.AIBrain")

class AstraBrain:
    def __init__(self, api_key=None):
        # Retrieve the API key from environment variables
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        if not self.api_key:
            logger.warning("GROQ_API_KEY environment variable is not set. ASTRA AI brain commands may fail.")
        self.client = Groq(api_key=self.api_key)
        self.history = []
        self.max_history = 10 # Retain last 10 messages (5 turns)
        self.system_prompt = (
            "You are ASTRA, a highly advanced, intelligent Jarvis-like desktop assistant created by Sanjeev. "
            "You have capabilities to run applications, manage files, open websites, and monitor system parameters. "
            "Keep your responses extremely helpful, concise, engaging, and professional."
        )

    def ask(self, question):
        """Adds question to history, calls LLM with conversation context, and returns reply."""
        self.history.append({"role": "user", "content": question})
        
        # Construct the payload starting with the system prompt followed by recent context history
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.history[-self.max_history:])
        
        try:
            logger.info("Sending prompt to Groq API with conversation context...")
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages
            )
            reply = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            logger.error(f"Groq API connection error: {str(e)}")
            # Remove the last user message if we failed to get a response
            if self.history:
                self.history.pop()
            return f"Sorry, I am having trouble connecting to my brain right now. Error details: {str(e)}"

    def clear_memory(self):
        """Clears the conversational context buffer."""
        self.history.clear()
        logger.info("Conversational memory cleared.")

# Instantiate global brain for backward compatibility with existing code
brain = AstraBrain()

def ask_astra(question):
    return brain.ask(question)
