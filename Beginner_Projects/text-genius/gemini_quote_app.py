import os
from google import genai
from dotenv import load_dotenv
load_dotenv()

# Initialize the client (reads GEMINI_API_KEY from environment automatically)
client = genai.Client()

def generate_psych_quote(theme_input):
    system_instruction = (
        "You are an expert in psychology, human behavior, and mindset-building. "
        "When given a theme, emotion, or topic, you must provide:\n"
        "1. A profound, original psychological quote about discipline, growth, or the mind.\n"
        "2. A short, summarized 2-3 sentence explanation breaking down the cognitive or psychological insight behind it."
    )

    prompt = f"Theme / Focus: {theme_input}"

    try:
        print("\nGenerating your psychological insight... Please wait...\n")
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "temperature": 0.8,
            }
        )
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

def main():
    print("=" * 60)
    print("🧠 TEXTGENIUS: GEMINI PSYCHOLOGICAL QUOTE GENERATOR 🧠")
    print("=" * 60)

    while True:
        theme = input("\nEnter a theme or topic (e.g., 'overcoming procrastination', 'mental resilience') or type 'exit' to quit:\n> ").strip()

        if theme.lower() == 'exit':
            print("Exiting generator. Keep building your mindset!")
            break

        if not theme:
            print("Please enter a valid theme.")
            continue

        result = generate_psych_quote(theme)
        
        print("-" * 60)
        print(result) 
        print("-" * 60)

if __name__ == "__main__":
    main()