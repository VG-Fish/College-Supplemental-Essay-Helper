from openai import OpenAI
from bs4 import BeautifulSoup
from typing import List, Set
import argparse, requests, validators, re

# Point to the local server
client: OpenAI = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
parser = argparse.ArgumentParser(description="Enter your prompt.")

parser.add_argument("url", help="Type in a specific college url (home page)", type=str)
parser.add_argument("interests", help="Type some of your interests.", type=str)
parser.add_argument("college", help="Type in the college/university you are interested in.", type=str)
parser.add_argument("MAX_URL_COUNT", help="Max amount of urls in the stack.", default=100, type=int)
parser.add_argument("MAX_URL_COUNT_QUIT", help="Max amount of times the stack can have max amount of urls before stopping.", default=10, type=int)

black_list: List[str] = ["youtube", "youtu.be", "facebook", "threads", "google"]
prompt: str = ""
response: str = ""

args = parser.parse_args()
MAX_URL_COUNT = args.MAX_URL_COUNT
# Max amount of times the stack can have max amount of urls before stopping.
MAX_URL_COUNT_QUIT = args.MAX_URL_COUNT_QUIT

college: str = args.college.lower()
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
    count: int = 0
    # We only want to increment count once during one iteration.
    count_incremented: bool = False
    context: List[str] = []
    stack: List[str] = []
    seen: Set[str] = set()
    stack.append(initial_url)

    while stack:
        curr_url = stack.pop()
        print(curr_url, len(stack), count)
        content = requests.get(curr_url).content
        soup = BeautifulSoup(content, "html.parser")
        context.append("\n".join(soup.get_text(separator=".", strip=True).split(".")) + ".\n")

        for tags in soup.find_all("a"):
            link = tags.get("href")
            if len(stack) == MAX_URL_COUNT and not count_incremented:
                count += 1
                count_incremented = True
            if len(stack) <= MAX_URL_COUNT and link not in seen and passed_link_check(link):
                stack.append(link)
                seen.add(link)
        
        count_incremented = False
        if count >= MAX_URL_COUNT_QUIT:
            break
    
    context.append(f"User interests: {interests}")
    return "Context: " + "\n".join(context)

def passed_link_check(link: str) -> bool:
    if not link:
        return False
    elif college not in link:
        return False
    
    for b_l in black_list:
        if b_l in link:
            return False
    # Check if valid url
    if not validators.url(link):
        return False
    return True

parse_college(url, interests)