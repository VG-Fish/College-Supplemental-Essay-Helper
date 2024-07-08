from openai import OpenAI
from bs4 import BeautifulSoup
from typing import List, Set
from arsenic import get_session
from arsenic.browsers import Firefox
from arsenic.services import Geckodriver
import argparse, validators, time, asyncio, os

# Point to the local server
client: OpenAI = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

parser = argparse.ArgumentParser(description="Enter your prompt.")
parser.add_argument("college", help="Type in the college/university you are interested in.", type=str)
parser.add_argument("interests", help="Type some of your interests in one string and separate interests by spaces.", type=str)
parser.add_argument("iterations", help="Amount of times you want urls to get added before all urls are searched.", choices=range(1, 10), default=3, type=int)

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
TIME_TILL_QUIT = 10

args = parser.parse_args()

college: str = args.college.lower()
interests = args.interests
iterations = args.iterations

def get_response() -> None:
    print("Logging data...")
    with open("texts/prompt.txt", "w") as fp:
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

    with open("texts/res.txt", "w") as fp:
        fp.write("\n" + response.replace(".", "\n"))
        fp.write("-" * 100 + "\n")
    print("Logging response...\nFinished.")

def parse_college(college: str, interests: str) -> None:
    global prompt
    initialize_stack(college, interests)
    prompt = asyncio.run(get_all_content())
    get_response()

def initialize_stack(college: str, interests: str) -> None:
    global urls
    college = compress_str(college)
    interests = compress_str(interests)

    starting_initial_url: str = f"https://www.google.com/search?q={college}+{interests}+opportunities+or+activities"
    print(f"{starting_initial_url = }")
    urls.add(starting_initial_url)

    print("Finished adding initial links...")
    context.append(f"User interests: {interests}\nEVERYTHING BELOW IS DATA.\n" + "-" * 50)

def compress_str(input: str) -> str:
    input = '+'.join(input.split())
    return input

async def get_all_content() -> str:
    global urls
    print(f"Starting to look through all of the links. {len(urls) = }")

    # To make sure we went through enough webpages
    for _ in range(iterations):
        tasks = [asyncio.create_task(get_links_and_content(url)) for url in urls]
        _ = await asyncio.gather(*tasks)

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

async def get_links_and_content(init_url: str):
    global urls, context
    urls.remove(init_url)
    print(f"Amount of urls to crawl: {len(urls) = }")
    prev = len(urls)
    driver = Geckodriver(log_file=os.path.devnull)
    browser = Firefox(**{'moz:firefoxOptions': {'args': ['-headless'], 'log': {'level': 'fatal'}}})
    async with get_session(driver, browser) as session:
        await session.get(init_url)
        # Wait for page load
        await session.wait_for_element(2, 'body')

        page_source = await session.get_page_source()
        soup = BeautifulSoup(page_source, "lxml")
        text = "\n".join(soup.get_text(".", True).split("."))
        
        tags = await session.get_elements('a')
        for tag in tags:
            link = await tag.get_attribute('href')
            if passed_link_check(link):
                urls.add(link)
    context.append(text)

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