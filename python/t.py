import aiohttp, asyncio, validators
from bs4 import BeautifulSoup
from concurrent.futures import ProcessPoolExecutor

college = "mit"
context = []
urls = {
    "https://www.media.mit.edu/research/?filter=everything&tag=mechatronics",
    "https://www.manipal.edu/mit/department-faculty/department-list/Copy%20of%20mechatronics.html",
    "https://www.manipal.edu/mit/department-faculty/department-list/mechatronics.html",
    "https://www.quora.com/Why-doesnt-MIT-offer-a-degree-in-machatronics?top_ans=97468990",
    "https://meche.mit.edu/about",
    "https://catalog.mit.edu/mit/campus-life/activities/",
    "https://mechatronics.mit.edu/",
    "https://mechatronics.mit.edu/projects/",
    "https://www.media.mit.edu/projects/dynamic-interfaces/overview/",
    "https://www.google.com/advanced_search?q=mit+mechatronics+opportunities+or+activities",
    "https://meche.mit.edu/featured-classes/mechatronics",
}
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

if __name__ == "__main__":
    asyncio.run(get_all_content())
    print(*urls, sep="\n")
    print(len(urls))