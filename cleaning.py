import re
from nltk import word_tokenize
from nltk.corpus import stopwords
import json

STOPWORDS = set(stopwords.words('english'))

def clean_text(text: str) -> str:
    # convert to lowercase
    lower_cased = text.lower()
    # remove references in square brackets
    no_references = re.sub(r'\[.*?\]', '', lower_cased)
    # keep only alphanumeric characters
    alphanumeric = re.sub(r'\W+', ' ', no_references)
    # remove stopwords
    no_stopwords = ' '.join([word for word in alphanumeric.split() if word not in STOPWORDS])
    return no_stopwords

def clean_page(page: dict) -> dict:
    # apply the clean_text function to each paragraph in the page
    cleaned_page = {}
    # clean the URL and title
    cleaned_page['url'], cleaned_page['title'] = page['url'], clean_text(page['title'])
    # clean the summary paragraphs
    if page['summary']:
        cleaned_page['summary'] = [clean_text(paragraph) for paragraph in page['summary']]
    # clean the content sections
    cleaned_page['content'] = []
    for section in page['content']:
        if not section['paragraphs']:
            continue
        cleaned_section = {}
        # clean the section title
        cleaned_section['title'] = clean_text(section['title'])
        # clean each paragraph in the section
        cleaned_section['paragraphs'] = [clean_text(paragraph) for paragraph in section['paragraphs'] if clean_text(paragraph)]
        cleaned_page['content'].append(cleaned_section)
    return cleaned_page

if __name__ == '__main__':
    # load the data
    with open('data/raw_wiki.json', 'r') as f:
        data = json.load(f)
    # clean each page
    cleaned_data = [clean_page(page) for page in data]
    # save the cleaned data
    with open('cleaned_data.json', 'w') as f:
        json.dump(cleaned_data, f, indent=4)