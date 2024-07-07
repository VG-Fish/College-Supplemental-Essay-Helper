from openai import OpenAI
from bs4 import BeautifulSoup
from typing import List, Set, Tuple
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import selenium.common.exceptions as selenium_exceptions
import argparse, validators, time

# Point to the local server
client: OpenAI = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
fire_fox_options = Options()
fire_fox_options.add_argument("--headless")

parser = argparse.ArgumentParser(description="Enter your prompt.")
parser.add_argument("college", help="Type in the college/university you are interested in.", type=str)
parser.add_argument("interests", help="Type some of your interests in one string and separate interests by spaces.", type=str)
parser.add_argument("MAX_URL_COUNT", help="Max amount of urls in the stack.", default=100, type=int)
parser.add_argument("MAX_URL_COUNT_QUIT", help="Max amount of times the stack can have max amount of urls before stopping.", default=10, type=int)

black_list: List[str] = [
    "youtube", 
    "youtu.be", 
    "facebook", 
    "threads", 
    "instagram", 
    "tiktok",
    "twitter",
    "calendar", 
    "mail", 
    "payment",
    "princetonreview",
    "sat",
    "login",
    "password",
    "register",
    "account",
    "comments"
]
system_context: str = """
Respond ONLY in plain text. NO MARKDOWN. BE CONCISE.
You need to help the user in finding relevant activities & opportunities a college has in a specific area. 
Make sure to pay attention to specific attention to 'User interests: ...' at the bottom of the prompts and tailor your response to the interests listed.
If the dad is unrelated to the user interests, respond back with 'Unable to help you with the task.'
DON'T BOTHER TO WRITE ABOUT SOMETHING UNRELATED.
You will be given a bunch of text that has been found on the college's web pages.
"""
context: List[str] = []
urls: Set[str] = set()
prompt: str = ""
response: str = ""

args = parser.parse_args()
MAX_URL_COUNT = args.MAX_URL_COUNT
# Max amount of times the stack can have max amount of urls before stopping.
MAX_URL_COUNT_QUIT = args.MAX_URL_COUNT_QUIT

college: str = args.college.lower()
interests = args.interests

def get_response() -> None:
    print("Logging data...")
    with open("logs.txt", "w") as fp:
        fp.write(prompt + "\n")
        fp.write("-" * 100 + "\n")
    
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
        fp.write("\n" + response.replace(".", "\n"))
        fp.write("-" * 100 + "\n")
    print("Logging response...\nFinished.")

def parse_college(college: str, interests: str) -> None:
    global prompt
    initialize_stack(college, interests)
    prompt = get_all_content()
    get_response()

def initialize_stack(college: str, interests: str) -> None:
    global urls
    college = compress_str(college)
    interests = compress_str(interests)

    starting_initial_url: str = f"https://www.google.com/search?q={college}+{interests}+opportunities+or+activities"
    print(f"{starting_initial_url = }")
    urls.add(starting_initial_url)

    urls, text = get_links_and_content(starting_initial_url)
    urls = urls.union(urls)
    context.append(text)

    print("Finished adding initial links...")
    context.append(f"User interests: {interests}\nEVERYTHING BELOW IS DATA.\n" + "-" * 50)

def compress_str(input: str) -> str:
    input = '+'.join(input.split())
    return input

def get_all_content() -> str:
    global urls
    print(f"Starting to look through all of the links. {len(urls) = }")
    count: int = 0
    running: bool = True
    while running:
        # Just in case
        if count >= MAX_URL_COUNT_QUIT:
            break

        print(f"\nNumber of urls to look through: {len(urls)}. Current {count = }")
        with ThreadPoolExecutor() as executor:
            for num, (urls, text) in enumerate(executor.map(get_links_and_content, urls)):
                if len(urls) >= MAX_URL_COUNT * MAX_URL_COUNT_QUIT:
                    context.append(text)
                    running = False
                    break

                print(f"Adding thread-{num} content...")
                urls = urls.union(res)
                context.append(text)

        if len(urls) >= MAX_URL_COUNT:
            count += 1
    print(f"Finished getting all the links. Need to get content from {len(urls)} urls.\n")
    
    with ProcessPoolExecutor() as executor:
        for num, res in enumerate(executor.map(get_url_content, urls)):
            print(f"Adding process-{num} content...")
            context.append(res)
    
    print("Finished looking through all of the links...")
    p = f'''
    "PROMPT: I AM A HIGHSCHOOL STUDENT WHO WANTS TO OPPORTUNITIES OR ACTIVITIES RELEVANT TO COLLEGE ADMISSIONS ESSAYS
    DO NOT GIVE GENERAL ADVICE
    USE THE DATA ABOVE TO FIND VERY VERY SPECIFIC THINGS I CAN USE
    THE MORE SPECIFIC TO {college}, THE BETTER
    BE SURE TO BE VERY SPECIFIC AND CONCISE "
    ''' + "Interests: " + interests.replace('+', ',')
    context.append(". ".join(p.split("\n")))
    return "Context: " + "\n".join(context)

def get_links_and_content(url: str) -> Tuple[Set[str], str]:
    driver = webdriver.Firefox(options=fire_fox_options)
    driver.set_page_load_timeout(20)
    try:
        driver.get(url)
        content = driver.page_source
    except (selenium_exceptions.WebDriverException, selenium_exceptions.TimeoutException) as e:
        print(url)
        print(e)
        return set()
    finally:
        driver.quit()
    
    soup = BeautifulSoup(content, "lxml")

    urls = set()
    for tag in soup.find_all("a", attrs={"jsname": "UWckNb"}) + soup.find_all("a"):
        link = tag.get("href")
        if passed_link_check(link):
            urls.add(link)

    driver.quit()
    return urls, soup.get_text(separator=".", strip=True)

def get_url_content(url: str) -> str:
    driver = webdriver.Firefox(options=fire_fox_options)
    driver.set_page_load_timeout(20)
    try:
        driver.get(url)
        content = driver.page_source
        soup = BeautifulSoup(content, "lxml")

        return soup.get_text(separator=".", strip=True)
    except (selenium_exceptions.WebDriverException, selenium_exceptions.TimeoutException) as e:
            return str(e)
    finally:
        driver.quit()

def passed_link_check(link: str) -> bool:
    if not link or not validators.url(link):
        return False
    
    link = link.lower()
    # Check if none of the words of the college are in the url.
    if sum((0 if word not in link else 1 for word in college.split())) == 0:
        return False

    for b_l in black_list:
        if b_l in link:
            return False
    return True

if __name__ == "__main__":
    start = time.time()
    parse_college(college, interests)
    end = time.time()

    print(f"Total time: {(end - start):2f}")
    with open("logs.txt", "a") as fp:
        fp.write(f"Total time: {(end - start):2f}\n")