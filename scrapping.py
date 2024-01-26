import requests
from bs4 import BeautifulSoup
import json
import time

class WikiPage():
    def __init__(self, url) -> None:
        self.url = url
        self.soup = self.get_soup()
        self.links = self.get_links()
        self.title = self.get_h1()
        self.content = self.get_content()[1:]
        self.summary = self.get_summary()

    def get_wiki_page(self) -> str:
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {self.url}: {e}")
            return None
        
    def get_soup(self) -> BeautifulSoup:
        page = self.get_wiki_page()
        soup = BeautifulSoup(page, "html.parser")
        return soup
    
    def get_links(self) -> list:
        allLinks = self.soup.find(id="bodyContent").find_all("a")
        # filter out links that don't have the href attribute
        links = [link for link in allLinks if link.has_attr("href")]
        # filter out links that have the href attribute but don't start with /wiki/
        links = [link for link in links if link["href"].find("/wiki/") == 0]
        # filter out links that are files (end with .jpg, .png, .svg)
        links = [link for link in links if link["href"].find(".jpg") == -1]
        links = [link for link in links if link["href"].find(".png") == -1]
        links = [link for link in links if link["href"].find(".svg") == -1]
        return [link["href"] for link in links]
    
    # Parser
    def get_h1(self) -> str:
        return self.soup.find(id="firstHeading").text
    
    def get_summary(self) -> list:
        try:
            if self.soup.find("table"):
                return [p.text for p in self.soup.find("table").find_next_siblings("p")]
            else:
                # if there is no table we must get the summary in another way
                # get the first 10 paragraphs
                summary = [p.text for p in self.soup.find_all("p")[:10]]
                # get the first paragraph of the content (that comes after the first h2)
                first_p = self.content[0]["paragraphs"]
                # return the summary that are not in the first paragraph
                return [p for p in summary if p not in first_p]
        except Exception as e:
            print(f"Error getting summary for {self.url}: {e}")
            return None
        
    
    def get_content(self) -> list:
        content = []
        tags = [f"h{n}" for n in range(2, 4)]
        # find all h2 or h3 tags
        for tag in self.soup.find_all(tags):
            paragraph = []
            # find all siblings of the tag until we find a new heading tag
            for sibling in tag.next_siblings:
                if sibling.name in tags:
                    break
                if sibling.name == "p":
                    paragraph.append(sibling.text)
            content.append({
                "type": tag.name,
                "title": tag.text,
                "paragraphs": paragraph
            })
        return content

    def wiki_page_to_dict(self):
        return {
            "url": self.url,
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
            "links": self.links
        }
    
    def to_json(self, filename="data/raw_wiki.json"):
        # add it to the existing file
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                data.append(self.wiki_page_to_dict())
        except:
            data = [self.wiki_page_to_dict()]
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

if __name__ == "__main__":
    start = time.time()
    print("Starting scrapping...")
    root_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    root_page = WikiPage(root_url)
    done = [root_url]
    fifo_links = root_page.links

    # while we don't have 100 links in our dictionary we will continue to loop
    while len(done) < 5000:
        link = fifo_links.pop(0)
        link_url = "https://en.wikipedia.org" + link
        if link_url in done:
            continue
        page = WikiPage(link_url)
        page.to_json()
        done.append(page.url)
        if len(fifo_links) + len(done) < 5000:
            # check the length of the total links to make sure we don't have too much links
            fifo_links = fifo_links + page.links
        if len(done) % 50 == 0:
            print(f"Done {len(done)} pages in {round(time.time() - start)} seconds. {len(fifo_links)} links remaining.")