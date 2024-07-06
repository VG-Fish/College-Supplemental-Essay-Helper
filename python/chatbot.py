from openai import OpenAI
from bs4 import BeautifulSoup
from typing import List
import argparse, requests, validators

# Point to the local server
client: OpenAI = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
parser = argparse.ArgumentParser(description="Enter your prompt.")
parser.add_argument("url", help="Type in a specific college url (home page)", type=str)
parser.add_argument("interests", help="Type some of your interests.", type=str)

black_list: List[str] = ["youtube", "youtu.be", "instagram", "tiktok"]
prompt: List[str] = ""
response: str = ""
MAX_URL_COUNT = 100


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
    get_all_content(url)

def get_all_content(initial_url: str):
    stack = []
    stack.append(initial_url)

    while stack:
        curr_url = stack.pop()
        print(len(stack), "\n")
        content = requests.get(curr_url).content
        soup = BeautifulSoup(content, "html.parser")
        #print(soup)
        
        for tags in soup.find_all("a"):
            link = tags.get("href")
            if len(stack) <= MAX_URL_COUNT and passed_black_list_check(link):
                stack.append(link)

def passed_black_list_check(link: str) -> bool:
    for b_l in black_list:
        if b_l in link:
            return False
    # Check if valid url
    if not validators.url(link):
        return False
    return True

def main() -> None:
    args = parser.parse_args()
    url = args.url
    interests = args.interests
    parse_college(url, interests)

if __name__ == "__main__":
    main()