from openai import OpenAI
from bs4 import BeautifulSoup
from typing import List, Set 
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import selenium.common.exceptions as selenium_exceptions
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
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

black_list: List[str] = ["youtube", "youtu.be", "facebook", "threads", "instagram", "tiktok", "twitter", "calendar", "mail", "payment"]
system_context: str = """
Respond ONLY in plain text. NO MARKDOWN. BE CONCISE.
You need to help the user in finding relevant activities & opportunities a college has in a specific area. 
Make sure to pay attention to specific attention to 'User interests: ...' at the bottom of the prompts and tailor your response to the interests listed.
If the dad is unrelated to the user interests, respond back with 'Unable to help you with the task.'
DON'T BOTHER TO WRITE ABOUT SOMETHING UNRELATED.
You will be given a bunch of text that has been found on the college's web pages.
"""
context: List[str] = []
stack: List[str] = []
seen: Set[str] = set()
prompt: str = ""
response: str = ""

args = parser.parse_args()
MAX_URL_COUNT = args.MAX_URL_COUNT
# Max amount of times the stack can have max amount of urls before stopping.
MAX_URL_COUNT_QUIT = args.MAX_URL_COUNT_QUIT

college: str = args.college.lower()
interests = args.interests

def get_response() -> None:
    print("Starting model inference...")
    completion = client.chat.completions.create(
        model="RichardErkhov/fblgit_-_una-cybertron-7b-v1-fp16-gguf",
        messages=[
        {"role": "system", "content": " ".join(system_context.split("\n"))},
        {"role": "user", "content": prompt}
        ]
    )
    response = completion.choices[0].message.content

    with open("res.txt", "a") as fp:
        fp.write(response.replace(".", "\n"))
        fp.write("-" * 100)

    with open("logs.txt", "a") as fp:
        fp.write(prompt + "\n")
        fp.write("-" * 100)

def parse_college(college: str, interests: str) -> None:
    global prompt
    initialize_stack(college, interests)
    prompt = get_all_content()
    get_response()

def initialize_stack(college: str, interests: str) -> None:
    college = compress_str(college)
    interests = compress_str(interests)

    initial_url: str = f"https://www.google.com/search?q={college}+{interests}+opportunities+or+activities"
    print(initial_url)
    driver.get(initial_url)

    context.append(f"User interests: {interests}\nEVERYTHING BELOW IS DATA.\n" + "-" * 50)

    # To get the first url from the google search and go from there.
    content: bytes = driver.page_source
    soup = BeautifulSoup(content, "lxml")
    initial_url = soup.find("a", attrs={"jsname": "UWckNb"}).get("href")
    stack.append(initial_url)
    seen.add(initial_url)
    driver.quit()

def compress_str(input: str) -> str:
    input = '+'.join(input.split())
    return input

def get_all_content() -> str:
    count: int = 0
    while stack:
        with ProcessPoolExecutor() as executor:
            for new_links, thread_seen in executor.map(get_all_urls, stack):
                stack.extend(new_links)
                seen.union(thread_seen)

        if len(stack) >= MAX_URL_COUNT:
            count += 1
        if count >= MAX_URL_COUNT_QUIT:
            break
    print(f"Finished getting all links.{len(stack) = }, {len(seen) = }, {count = }")
    
    with ThreadPoolExecutor() as executor:
        for result in executor.map(get_url_content, stack):
            context.append(result)
    print("Finished looking through all of the links...")
    p = '''
    "PROMPT: I AM A HIGHSCHOOL STUDENT WHO WANTS TO OPPORTUNITIES OR ACTIVITIES RELEVANT TO COLLEGE ADMISSIONS ESSAYS
    DO NOT GIVE GENERAL ADVICE
    USE THE DATA ABOVE TO FIND VERY VERY SPECIFIC THINGS I CAN USE
    THE MORE SPECIFIC, THE BETTER
    BE SURE TO BE VERY SPECIFIC AND CONCISE "
    ''' + "Interests: " + interests.replace('+', ',')
    context.append(". ".join(p.split("\n")))
    return "Context: " + "\n".join(context)

def get_all_urls(url: str) -> List[str]:
    global seen
    new_links, thread_seen = [], seen
    driver = webdriver.Firefox(options=fire_fox_options)

    try:
        driver.get(url)
        content = driver.page_source
    except selenium_exceptions.WebDriverException as e:
        print(e)
        return []
    
    soup = BeautifulSoup(content, "lxml")
    for tag in soup.find_all("a"):
        link = tag.get("href")
        if link not in seen and passed_link_check(link):
            thread_seen.add(link)
            new_links.append(link)
    return new_links, thread_seen

def get_url_content(url: str) -> str:
    driver = webdriver.Firefox(options=fire_fox_options)
    try:
        driver.get(url)
        content = driver.page_source
        soup = BeautifulSoup(content, "lxml")

        return ".\n".join(soup.get_text(separator=".", strip=True).split("."))
    except selenium_exceptions.WebDriverException as e:
            return str(e)
    finally:
        driver.quit()

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

if __name__ == "__main__":
    parse_college(college, interests)