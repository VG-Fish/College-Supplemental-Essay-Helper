import aiohttp, asyncio, validators, time, os, re
from arsenic.browsers import Firefox
from arsenic.services import Geckodriver
from arsenic import get_session
from bs4 import BeautifulSoup
from concurrent.futures import ProcessPoolExecutor
from typing import Set, List, Tuple
from typing_extensions import Self

class Crawler():
    def __init__(self: Self, college: str, interests: str) -> None:
        self.black_list: List[str] = ["youtube", "youtu.be", "facebook", "threads", "instagram", "tiktok","twitter","calendar", "mail", "payment","princetonreview","sat","login","password","register","account","comments","maps","linkedin","manipal"]
        self.college: str = college
        self.interests: str = interests
        self.context: List[str] = []
        self.urls: Set[str] = set()

    def get_links_and_urls(self: Self, html: str) -> Tuple[Set[str], str]:
        soup = BeautifulSoup(html, "lxml")
        urls, text = set(), ""
        text = "\n".join(soup.get_text(".", True).split("."))

        for tag in soup.find_all("a"):
            link = tag.get("href")
            if self.passed_link_check(link):
                urls.add(link)
        
        return urls, text

    def passed_link_check(self: Self, link: str) -> bool:
        if not link or not validators.url(link):
            return False
        
        link = self.sanitize_link(link.lower())

        for b_l in self.black_list:
            if b_l in link:
                return False

        college_words = self.college.split()
        for c_w in college_words:
            if c_w in link:
                return True
        return False

    def sanitize_link(self: Self, link: str) -> str:
        if not link:
            return
        link = re.sub(":\d+", "", link)
        return link

    async def get_initial_links(self: Self, url: str) -> None:
        driver = Geckodriver(log_file=os.path.devnull)
        browser = Firefox(**{'moz:firefoxOptions': {'args': ['-headless']}})

        try:
            async with get_session(driver, browser) as session:
                await session.get(url)
                # Wait for page load
                await session.wait_for_element(2, 'body')

                page_source = await session.get_page_source()
                soup = BeautifulSoup(page_source, "lxml")
                text = "\n".join(soup.get_text(".", True).split("."))
                
                tags = await session.get_elements('a')
                for tag in tags:
                    link = await tag.get_attribute('href')
                    if self.passed_link_check(link):
                        self.urls.add(link)
            self.context.append(text)
        except TimeoutError as e:
            print(f"TIMEOUT ERROR! {e}")
    
    async def get_text(self: Self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, ssl=False) as response:
                    if response.status == 200:
                        return await response.text()
            except (aiohttp.ClientConnectorSSLError, UnicodeDecodeError, aiohttp.ServerDisconnectedError, aiohttp.ClientOSError) as e:
                print(f"ERROR! {e}")
                return ""

    async def get_all_content(self: Self) -> None:
        tasks = [asyncio.create_task(self.get_text(url)) for url in self.urls]
        texts = await asyncio.gather(*tasks)
        # Get rid of empty strings
        texts = list(filter(None, texts))
        self.urls.clear()

        print("Finished receiving the html of all urls. Now scraping the urls.")

        with ProcessPoolExecutor() as executor:
            results = executor.map(self.get_links_and_urls, texts)
            for result in results:
                self.urls.update(result[0])
                self.context.append(result[1])

        with open("texts/logs.txt", "w") as fp:
            for num, url in enumerate(self.urls):
                fp.write(f"URL {num}: {url}\n")
        
        with open("texts/prompt.txt", "w") as fp:
            fp.write(self.get_context())
        
        print("Finished task.")
    
    def get_context(self: Self) -> str:
        return "\n".join(self.context)
    
    def write_to_file(self: Self, path: str, time: float | None = None) -> None:
        if path == "texts/time.txt" and time:
            with open(path, "w") as fp:
                fp.write(f"TOTAL TIME: {time:2f}s\n" + "-" * 50 + "\n")
        elif path == "texts/logs.txt":
            with open("texts/logs.txt", "w") as fp:
                fp.write(f"{self.urls}\n")
                fp.write(f"{len(self.urls) = }")

async def main() -> None:
    college: str = "MIT"
    interests: str = "mechatronics"
    await run(college, interests)

async def run(college: str, interests: str) -> None:
    start: float = time.perf_counter()

    crawler: Crawler = Crawler(college, interests)

    await crawler.get_initial_links(f"https://www.google.com/search?q={college}+{interests}+opportunities+or+activities")
    for i in range(3):
        await crawler.get_all_content()
    
    end: float = time.perf_counter()
    crawler.write_to_file("texts/time.txt", end - start)

if __name__ == "__main__":
   asyncio.run(main())