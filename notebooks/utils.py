import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

STOPWORDS = set(stopwords.words('english'))

def clean_text(text: str) -> str:
    # convert to lowercase
    lower_cased = text.lower()
    # remove references in square brackets
    no_references = re.sub(r'\[.*?\]', '', lower_cased)
    # keep only alphanumeric characters
    alphanumeric = re.sub(r'\W+', ' ', no_references)
    # remove strange unicode characters
    alphanumeric = re.sub(r'[^\x00-\x7F]+', '', alphanumeric)
    # remove stopwords
    no_stopwords = ' '.join([word for word in alphanumeric.split() if word not in STOPWORDS])
    # stemmize
    stemmed = ' '.join([PorterStemmer().stem(word) for word in no_stopwords.split()])
    return stemmed

def get_n_gram(n, text):
    # get word n_gram
    words = text.split()
    n_gram = []
    for i in range(len(words) - n + 1):
        n_gram.append(' '.join(words[i:i+n]))
    return n_gram