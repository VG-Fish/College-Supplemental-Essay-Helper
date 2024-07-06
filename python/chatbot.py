from openai import OpenAI
from bs4 import BeautifulSoup
from typing import List
import argparse, requests, validators, re

# Point to the local server
client: OpenAI = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
parser = argparse.ArgumentParser(description="Enter your prompt.")
parser.add_argument("url", help="Type in a specific college url (home page)", type=str)
parser.add_argument("interests", help="Type some of your interests.", type=str)
parser.add_argument("MAX_URL_COUNT", help="Max amount of urls in the stack.", default=100, type=int)
parser.add_argument("MAX_URL_COUNT_QUIT", help="Max amount of times the stack can have max amount of urls before stopping.", default=3, type=int)

black_list: List[str] = ["youtube", "youtu.be"]
prompt: str = ""
response: str = ""

args = parser.parse_args()
MAX_URL_COUNT = args.MAX_URL_COUNT
# Max amount of times the stack can have max amount of urls before stopping.
MAX_URL_COUNT_QUIT = args.MAX_URL_COUNT_QUIT
url = args.url
interests = args.interests

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
    prompt = get_all_content(url, interests)
    print(prompt)

def get_all_content(initial_url: str, interests: str) -> str:
    count = 0
    context: List[str] = []
    stack = []
    stack.append(initial_url)

    while stack:
        curr_url = stack.pop()
        content = requests.get(curr_url).content
        soup = BeautifulSoup(content, "html.parser")
        context.append(" ".join(soup.get_text().split()) + ".")
        
        for tags in soup.find_all("a"):
            link = tags.get("href")
            if len(stack) <= MAX_URL_COUNT and passed_black_list_check(link):
                stack.append(link)
            if len(stack) == MAX_URL_COUNT:
                count += 1
        
        if count == MAX_URL_COUNT_QUIT:
            break
    
    context.append(f"{interests = }")
    return "Context: " + "\n".join(context)

def passed_black_list_check(link: str) -> bool:
    for b_l in black_list:
        if b_l in link:
            return False
    # Check if valid url
    if not validators.url(link):
        return False
    return True

parse_college(url, interests)