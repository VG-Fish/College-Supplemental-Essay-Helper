from openai import OpenAI
from bs4 import BeautifulSoup
from typing import List, Set 
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import argparse, validators

# Point to the local server
client: OpenAI = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
fire_fox_options = Options()
fire_fox_options.add_argument("--headless")
driver = webdriver.Firefox(options=fire_fox_options)

parser = argparse.ArgumentParser(description="Enter your prompt.")
parser.add_argument("college", help="Type in the college/university you are interested in.", type=str)
parser.add_argument("interests", help="Type some of your interests in one string and separate interests by spaces.", type=str)
parser.add_argument("MAX_URL_COUNT", help="Max amount of urls in the stack.", default=100, type=int)
parser.add_argument("MAX_URL_COUNT_QUIT", help="Max amount of times the stack can have max amount of urls before stopping.", default=10, type=int)

black_list: List[str] = ["youtube", "youtu.be", "facebook", "threads", "google", "calendar"]
system_context: str = """
Respond ONLY in plain text. NO MARKDOWN. BE CONCISE.
You need to help the user in finding relevant activities & opportunities a college has in a specific area. 
Make sure to pay attention to specific attention to 'User interests: ...' at the bottom of the prompts and tailor your response to the interests listed.
If the dad is unrelated to the user interests, respond back with 'Unable to help you with the task.'
DON'T BOTHER TO WRITE ABOUT SOMETHING UNRELATED.
You will be given a bunch of text that has been found on the college's web pages.
"""
prompt: str = ""
response: str = ""

args = parser.parse_args()
MAX_URL_COUNT = args.MAX_URL_COUNT
# Max amount of times the stack can have max amount of urls before stopping.
MAX_URL_COUNT_QUIT = args.MAX_URL_COUNT_QUIT

college: str = args.college.lower()
interests = args.interests

def get_response() -> None:
    print(prompt)
    print("Generated Response:\n")
    completion = client.chat.completions.create(
        model="RichardErkhov/fblgit_-_una-cybertron-7b-v1-fp16-gguf",
        messages=[
        {"role": "system", "content": " ".join(system_context.split("\n"))},
        {"role": "user", "content": prompt}
        ]
    )
    response = completion.choices[0].message.content
    print(response)

def parse_college(college: str, interests: str) -> None:
    global prompt
    prompt = get_all_content(college, interests)
    get_response()

def get_all_content(college: str, interests: str) -> str:
    interests = interests.replace(' ', '+')
    initial_url: str = f"https://www.google.com/search?q={college}+{interests}+opportunities"
    driver.get(initial_url)

    context: List[str] = []
    context.append(f"User interests: {interests}\nEVERYTHING BELOW IS DATA.\n" + "-" * 50)

    # To get the first url from the google search and go from there.
    content: bytes = driver.page_source
    soup = BeautifulSoup(content, "lxml")
    initial_url = soup.find("a", attrs={"jsname": "UWckNb"}).get("href")
 
    count: int = 0
    # We only want to increment count once during one iteration.
    count_incremented: bool = False
    stack: List[str] = []
    seen: Set[str] = set()
    stack.append(initial_url)
    seen.add(initial_url)

    while stack:
        curr_url: str = stack.pop()
        print(curr_url, len(stack), count)

        driver.get(curr_url)
        content = driver.page_source

        soup = BeautifulSoup(content, "lxml")
        context.append(".\n".join(soup.get_text(separator=".", strip=True).split(".")))

        for tags in soup.find_all("a"):
            link = tags.get("href")
            if len(stack) == MAX_URL_COUNT and not count_incremented:
                count += 1
                count_incremented = True
            if len(stack) <= MAX_URL_COUNT and count < MAX_URL_COUNT_QUIT and link not in seen and passed_link_check(link):
                stack.append(link)
                seen.add(link)
        
        count_incremented = False
    
    driver.quit()
    context.append("PROMPT: FIND ME OPPORTUNITIES OR ACTIVITIES IN THE DATA GIVEN ABOVE THAT I CAN WRITE ABOUT IN COLLEGE ADMISSIONS. BE SURE TO BE SPECIFIC. {}".format(interests.replace('+', ',')))
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

parse_college(college, interests)