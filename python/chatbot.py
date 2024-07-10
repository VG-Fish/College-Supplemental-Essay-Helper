from openai import OpenAI
from bs4 import BeautifulSoup
from typing import List, Set, Tuple
import argparse, validators, time, asyncio, aiohttp

# Point to the local server
client: OpenAI = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

parser = argparse.ArgumentParser(description="Enter your prompt.")
parser.add_argument("college", help="Type in the college/university you are interested in.", type=str)
parser.add_argument("interests", help="Type some of your interests in one string and separate interests by spaces.", type=str)
parser.add_argument("iterations", help="Amount of times you want urls to get added before all urls are searched.", choices=range(1, 10), default=2, type=int)

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
DON'T BOTHER TO WRITE ABOUT SOMETHING UNRELATED.
You will be given a bunch of text that may contain irrelevant information.
"""
context: List[str] = []
urls: Set[str] = set()
prompt: str = ""
response: str = ""

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

    with open("texts/result.txt", "w") as fp:
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
    # Remove old urls
    #urls = urls.difference(old_urls)
    print(f"CURRENT LINKS ({len(urls) = }):\n")
    print(*urls, sep="\n")
    end = time.perf_counter()

    with open("texts/time.txt", "a") as fp:
        fp.write(f"Crawling time: {(end - start):2f}\n")
    print("Finished looking through all of the links...")

    p = f'''
    I AM A HIGHSCHOOL STUDENT WHO WANTS TO OPPORTUNITIES OR ACTIVITIES RELEVANT TO COLLEGE ADMISSIONS ESSAYS
    DO NOT GIVE GENERAL ADVICE
    FOR EXAMPLE, CITE OPPORTUNITIES OR ACTIVITIES THAT ARE RELEVANT TO {interests} THAT IS OFFERED by {college} THAT CAN BE DONE BY A HIGHSCHOOLER
    MAKE SURE THE OPPORTUNITIES OR ACTIVITIES ARE UNIQUE TO {college}
    TRY TO CITE AT-LEAST 7 OPPORTUNITIES OR ACTIVITIES
    MAKE SURE THE OPPORTUNITIES OR ACTIVITIES CAN BE DONE IN PERSON OR VIRTUALLY BY THE INTERNET
    BE SURE TO BE VERY SPECIFIC AND CONCISE AND THAT THEY CAN BE DONE BY A HIGHSCHOOLER
    ''' + "Interests: " + interests.replace('+', ',')
    context.append(". ".join(p.split("\n")))
    return "Context: " + "\n".join(context)

async def get_links_and_content(url: str) -> Tuple[List[str], Set[str]]:
    global context, urls
    async with aiohttp.ClientSession() as session:
        # asyncio.create_task() will throw all the tasks onto the event loop so asyncio.gather() just has to wait for responses.
        tasks = [asyncio.create_task(session.get(url, ssl=False)) for url in urls]
        responses = await asyncio.gather(*tasks)
        for response in responses:
            print(response)

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
    start = time.perf_counter()
    parse_college(college, interests)
    end = time.perf_counter()

    print(f"Total time: {(end - start):2f}")
    with open("texts/time.txt", "a") as fp:
        fp.write(f"Total time: {(end - start):2f}\n" + "-" * 50 + "\n")