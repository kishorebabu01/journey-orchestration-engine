# ============================================================
# FILE: agent/groq_client.py
# PURPOSE: Handles communication with the Groq API.
# ============================================================

import os
import json
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Default model used for generation
MODEL = "llama-3.3-70b-versatile"


def call_llama(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7
) -> dict:
    """
    Send a prompt to the Groq-hosted LLaMA model and return
    the response as a Python dictionary.

    Args:
        system_prompt: Instructions that define the model's role.
        user_prompt: The task or request to process.
        temperature: Controls response creativity.

    Returns:
        A parsed JSON response as a dictionary.
        If parsing fails, returns the raw response.
        If the API call fails, returns an error dictionary.
    """

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=1000,
        )

        raw_text = response.choices[0].message.content

        try:
            clean = raw_text.strip()

            # Remove Markdown code fences if present
            if clean.startswith("```"):
                lines = clean.split("\n")
                clean = "\n".join(lines[1:-1])

            return json.loads(clean)

        except json.JSONDecodeError:
            print("Warning: Failed to parse JSON response.")
            return {
                "raw_response": raw_text,
                "parse_error": True
            }

    except Exception as e:
        print(f"Groq API error: {e}")
        return {
            "error": str(e)
        }