import requests
from bs4 import BeautifulSoup


def print_google_doc_grid(url):
    # Fetch the published Google Doc page
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the first table in the document
    table = soup.find('table')
    if table is None:
        print("No table found in the document.")
        return

    # Parse the data rows to extract coordinates and characters
    grid = {}
    max_x = max_y = 0

    rows = table.find_all('tr')[1:]  # Skip header
    for row in rows:
        cols = row.find_all(['td', 'th'])
        if len(cols) != 3:
            continue  # Skip malformed rows
        x = int(cols[0].text.strip())
        ch = cols[1].text.strip()
        y = int(cols[2].text.strip())
        grid[(x, y)] = ch
        max_x = max(max_x, x)
        max_y = max(max_y, y)

    # Print the grid row by row (y increases downward)
    for y in range(max_y + 1):
        line = ''
        for x in range(max_x + 1):
            line += grid.get((x, y), ' ')
        print(line)


# Example usage with the provided URL
print_google_doc_grid(
    'https://docs.google.com/document/d/e/2PACX-1vTER-wL5E8YC9pxDx43gk8eIds59GtUUk4nJo_ZWagbnrH0NFvMXIw6VWFLpf5tWTZIT9P9oLIoFJ6A/pub')
