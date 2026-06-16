from bs4 import BeautifulSoup
import requests
import re

def get_difficulty(shortname: str) -> float:
    try:
        url = f"https://open.kattis.com/problems/{shortname}"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        diff_element = soup.find('span', class_='difficulty_number')
        # The difficulty can be a single value ("3.4") or a range ("1.7 - 1.9").
        # Pull out every number and take the max for ranges.
        numbers = [float(n) for n in re.findall(r'\d+(?:\.\d+)?', diff_element.text)]
        if not numbers:
            return None
        return max(numbers)
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

if __name__ == "__main__":
    shortname = "excludescoring"
    difficulty = get_difficulty(shortname)
    print(f"Difficulty for {shortname}: {difficulty}")
