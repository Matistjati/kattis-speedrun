from bs4 import BeautifulSoup
import requests

def get_difficulty(shortname: str) -> str:
    try:
        url = f"https://open.kattis.com/problems/{shortname}"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        diff_element = soup.find('span', class_='difficulty_number')
        return float(diff_element.text.strip())
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

if __name__ == "__main__":
    shortname = "excludescoring"
    difficulty = get_difficulty(shortname)
    print(f"Difficulty for {shortname}: {difficulty}")
