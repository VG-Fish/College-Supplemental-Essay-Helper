from openai import OpenAI
from bs4 import BeautifulSoup
import argparse

# Point to the local server
client: OpenAI = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
parser = argparse.ArgumentParser(description="Enter your prompt.")
parser.add_argument("prompt", help="Type in a specific college name and some of your interests.", type=str)

prompt: str = ""
response: str = ""

def get_response() -> None:
    completion = client.chat.completions.create(
        model="LM Studio Community/Phi-3-mini-4k-instruct-GGUF",
        messages=[
        {"role": "system", "content": "You need to help the user in finding relevant activities & opportunities a college has in a specific area."},
        {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    response = completion.choices[0].message.content

def parse_college(prompt: str) -> None:
    prompt = prompt

def main() -> None:
    args = parser.parse_args()
    prompt = args.prompt
    parse_college(prompt)

if __name__ == "__main__":
    main()