from openai import OpenAI
from bs4 import BeautifulSoup
from typing import List
import argparse, requests

# Point to the local server
client: OpenAI = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
parser = argparse.ArgumentParser(description="Enter your prompt.")
parser.add_argument("url", help="Type in a specific college url (home page)", type=str)
parser.add_argument("interests", help="Type some of your interests.", type=str)

prompt: List[str] = ""
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

def parse_college(url: str, interests: str) -> None:
    """All the urls to be searched."""
    get_all_content(url)

def get_all_content(initial_url: str):
    stack = []
    

def main() -> None:
    args = parser.parse_args()
    url = args.url
    interests = args.interests
    parse_college(url, interests)

if __name__ == "__main__":
    main()