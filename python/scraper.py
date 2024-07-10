import aiohttp, asyncio, validators, time
from bs4 import BeautifulSoup
from concurrent.futures import ProcessPoolExecutor

college = "mit"
context = []
urls = {}
black_list = [
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
    "comments",
    "maps",
    "linkedin",
    "manipal"
]

async def get_text(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, ssl=False) as response:
                if response.status == 200:
                    return await response.text()
        except (aiohttp.ClientConnectorSSLError, UnicodeDecodeError) as e:
            print(f"ERROR! {e}")
            return ""

def get_links_and_urls(html):
    soup = BeautifulSoup(html, "lxml")
    urls, text = set(), ""
    text = "\n".join(soup.get_text(".", True).split("."))

    for tag in soup.find_all("a"):
        link = tag.get("href")
        if passed_link_check(link):
            urls.add(link)
    
    return urls, text

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
    
async def get_all_content():
    tasks = [asyncio.create_task(get_text(url)) for url in urls]
    texts = await asyncio.gather(*tasks)
    # Get rid of empty strings
    texts = list(filter(None, texts))
    urls.clear()

    with ProcessPoolExecutor() as executor:
        results = executor.map(get_links_and_urls, texts)
        for result in results:
            urls.update(result[0])
            context.append(result[1])

async def main():
    start = time.perf_counter()
    asyncio.run(get_all_content())
    end = time.perf_counter()
    with open("texts/time.txt", "w") as fp:
        fp.write(f"{end - start:2f}")
    
    with open("texts/log.txt", "w") as fp:
        fp.write(f"{urls}\n")
        fp.write(len(urls))

if __name__ == "__main__":
    main()