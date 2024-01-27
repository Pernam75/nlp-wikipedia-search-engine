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
        links = [link["href"] for link in allLinks
                # check if it has an href attribute
                if link.has_attr("href") 
                # check if it is a wikipedia link
                and link["href"].startswith("/wiki/")
                # check if it is not a file 
                and not link["href"].endswith((".jpg", ".png", ".svg"))
                # check if it is not a special page
                and "Special:" not in link["href"]
                # check if it is not a help page
                and "Help:" not in link["href"] 
                # check if it is not a wikipedia page
                and "Wikipedia:" not in link["href"]]
        return links
    
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
        }
    
    def to_json(self, filename="data/raw_wiki.json"):
        # add it to the existing file
        with open(filename, "r") as f:
            data = json.load(f)
            data.append(self.wiki_page_to_dict())
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        

    def links_to_json(self, filename="data/links.json"):
        # add it to the existing file
        with open(filename, "r") as f:
            data = json.load(f)
            data.append({
                "url": self.url,
                "links": self.links
            })
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)  

if __name__ == "__main__":
    start = time.time()
    print("Starting scrapping...")
    root_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    root_page = WikiPage(root_url)
    # write the root page to the json file
    with open("data/raw_wiki.json", "w") as f:
        json.dump([root_page.wiki_page_to_dict()], f, indent=4)
    # write the root page links to the json file
    with open("data/links.json", "w") as f:
        json.dump([{
            "url": root_url,
            "links": root_page.links
        }], f, indent=4)
    done = [root_url]
    fifo_links = root_page.links

    # while we don't have 5000 pages in the json file we continue
    while len(done) < 5000:
        link = fifo_links.pop(0)
        try:
            link_url = "https://en.wikipedia.org" + link
            if link_url in done:
                continue
            page = WikiPage(link_url)
            page.to_json()
            page.links_to_json()
            done.append(page.url)
            if len(fifo_links) + len(done) < 5000:
                # check the length of the total links to make sure we don't have too much links
                fifo_links = fifo_links + page.links
        except Exception as e:
            print(f"Error getting {link_url}: {e}")
        if len(done) % 50 == 0:
            print(f"Done {len(done)} pages in {round(time.time() - start)} seconds. {len(fifo_links)} links remaining.")