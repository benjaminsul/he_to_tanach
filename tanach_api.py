# text utils: https://github.com/TechnionTDK/jbs-data/blob/master/raw2json/text_utils.py
import re
from typing import List, Any
import requests
import json
import os

import unicodedata

# extracted from get_tanakh_titles, is not expected to change...
TANACH_BOOKS = ['Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 'I Samuel', 'II Samuel',
                'I Kings', 'II Kings', 'Isaiah', 'Jeremiah', 'Ezekiel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah',
                'Micah', 'Nahum', 'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi', 'Psalms', 'Proverbs',
                'Job', 'Song of Songs', 'Ruth', 'Lamentations', 'Ecclesiastes', 'Esther', 'Daniel', 'Ezra', 'Nehemiah',
                'I Chronicles', 'II Chronicles']


# get json from https://www.sefaria.org/api/index/
# search for an object with "category" field equal to "Tanakh"
# Within its "contents" field, search for objects with "category" field equal to "Torah", "Prophets", "Writings".
# Within each of these objects, extract the "title" field from the "contents" array.
# return a list of strings
def get_tanakh_books(he=False) -> List[str]:
    url = "https://www.sefaria.org/api/index/"
    response = requests.get(url)
    json_data = json.loads(response.text)
    titles = []
    for item in json_data:
        if item["category"] == "Tanakh":
            for content_item in item["contents"]:
                if content_item["category"] in ["Torah", "Prophets", "Writings"]:
                    for title in content_item["contents"]:
                        if he:
                            titles.append(title["heTitle"])
                        else:
                            titles.append(title["title"])
    return titles


def get_parashot(book: str, he=False) -> [List[str], List[str]]:
    # call https://www.sefaria.org/api/index/{title}
    # extract the "sections" field, and return it
    url = f"https://www.sefaria.org/api/index/{book}"
    response = requests.get(url)
    json_data = json.loads(response.text)

    # get "alts"/"Parasha"/"nodes" list. Extract from each item the "title" field
    parashot = []
    refs = []
    for item in json_data["alts"]["Parasha"]["nodes"]:
        if he:
            parashot.append(item["heTitle"])
        else:
            parashot.append(item["title"])
        refs.append(item["wholeRef"])

    return parashot, refs


def get_num_of_chapters(book: str) -> int:
    # call https://www.sefaria.org/api/index/{title}
    # extract the "schema" field, and from it the "lengths" field, and return its first element
    url = f"https://www.sefaria.org/api/index/{book}"
    response = requests.get(url)
    json_data = json.loads(response.text)
    return json_data["schema"]["lengths"][0]


def get_psukim(title: str, chapter: int) -> List[str]:
    # call https://www.sefaria.org/api/texts/{title}.{chapter}
    # extract the "he" field, and return it
    url = f"https://www.sefaria.org/api/texts/{title}.{chapter}"
    response = requests.get(url)
    json_data = json.loads(response.text)
    return json_data["he"]


def get_commentaries(book: str, chapter: int, pasuk: int) -> list[tuple[Any, Any]]:
    # call https://www.sefaria.org/api/links/{title}.{chapter}.{pasuk}
    # extract objects with "category" field equal to "Commentary"
    # extract the "heTitle" and "he" fields from each of these objects.
    # return a list of tuples (heTitle, he)
    url = f"https://www.sefaria.org/api/links/{book}.{chapter}.{pasuk}"
    response = requests.get(url)
    json_data = json.loads(response.text)
    commentaries = []
    for item in json_data:
        if item["category"] == "Commentary":
            book = item["collectiveTitle"]["he"]
            text = item["he"]
            # if text is a list, join it into a string
            if isinstance(text, list):
                text = " ".join(text)
            # if item has no "heTitle" or "he" fields, print a warning and continue
            if len(book) == 0 or len(text) == 0:
                print(f"WARNING: item {item} has empty title or text")
                continue
            commentaries.append((book, text))
    return commentaries


def clean_text(text: str) -> str:
    # remove all but plain hebrew letters, and spaces
    # remove also english letters, numbers, and punctuation
    # return the cleaned text

    # replace - with space
    text = text.replace("-", " ")
    # remove multiple spaces with single space
    text = " ".join(text.split())

    return _strip_html(_remove_nikud(text))


def _strip_html(text: str) -> str:
    text = re.sub('<[^<]+?>', '', text)
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    return text


def _remove_nikud(text: str) -> str:
    """https://writing.stackexchange.com/questions/32470/how-do-i-remove-nikkud-vowel-marks-from-a-word-2016-document"""
    normalized = unicodedata.normalize('NFKD', text)
    no_nikkud = ''.join([c for c in normalized if not unicodedata.combining(c)])
    no_nikkud = no_nikkud.replace('־', ' ')  # our addition, a weird character found in texts
    no_nikkud = re.sub(r'&\w+;', '', no_nikkud)  # remove html entities
    no_nikkud = re.sub(r'׀', '', no_nikkud)
    no_nikkud = re.sub(r'{פ}', '', no_nikkud)
    no_nikkud = re.sub(r'{ס}', '', no_nikkud)
    no_nikkud = re.sub(r':', '', no_nikkud)
    return no_nikkud


# main block
if __name__ == "__main__":
    books = get_tanakh_books()
    for book in books:
        if book == "Daniel":
            continue
        num_of_chapters = get_num_of_chapters(book)
        book_folder = os.path.join('tanah', book)
        os.makedirs(book_folder, exist_ok=True)
        for chapter in range(1, num_of_chapters + 1):
            
                psukim = get_psukim(book, chapter)
                filename = os.path.join(book_folder, f"chapter_{chapter}.txt")
                with open(filename, "w", encoding="utf-8") as f:
                    for pasuk in psukim:
                        f.write(clean_text(pasuk) + "\n")
