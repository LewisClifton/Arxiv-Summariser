import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse


def fetch_abstract(arxiv_url):
    # Fetch the arXiv page content using requests
    response = requests.get(arxiv_url)
    if response.status_code != 200:
        return f"Error: Unable to fetch {arxiv_url}, status code: {response.status_code}"

    # Parse the HTML content of the arXiv page
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the abstract section
    abstract_tag = soup.find('blockquote', class_='abstract mathjax')
    if abstract_tag:
        # Get the content of the abstract and ensure a space after the "Abstract:" label
        abstract_text = abstract_tag.text.strip()
        # Ensure "Abstract:" has a space
        if abstract_text.startswith("Abstract:"):
            abstract_text = abstract_text.replace("Abstract:", "Abstract: ")
        return abstract_text
    else:
        return "Error: Abstract not found."

def summarise_with_gemini(abstract_text):
    # Set up the API endpoint for Gemini
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
    
    headers = {
        "Content-Type": "application/json",
    }

    # Create the payload to send the abstract to Gemini with a more focused prompt
    data = {
        "contents": [{
            "parts": [{
                "text": f"summarise the following abstract in 1-2 simple sentences. Focus on what the authors did, why, and the results: \n\n{abstract_text}"
            }]
        }]
    }

    # Make the POST request to the Gemini API
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        # Extract the summary from the response
        result = response.json()
        try:
            # Access the correct keys in the response structure
            summary = result['candidates'][0]['content']['parts'][0]['text']
            return summary
        except KeyError as e:
            return f"KeyError: {e}, check the response structure."
    else:
        return f"Error: Unable to get response, status code: {response.status_code}"


def fetch_papers_for_date_range(keyword, start_date, end_date, max_results):
    papers = []
    # Convert keyword to query-friendly format
    query = f'all:{keyword.replace(" ", "+")}'
    query_url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results={max_results}"

    response = requests.get(query_url)
    if response.status_code != 200:
        print(f"Error: Unable to fetch papers for keyword '{keyword}', status code: {response.status_code}")
        return papers

    root = ET.fromstring(response.content)
    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
        title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
        summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
        link = entry.find('{http://www.w3.org/2005/Atom}link[@title="pdf"]').attrib['href']
        papers.append({'title': title, 'summary': summary, 'link': link, 'keyword': keyword})

    return papers


def fetch_papers(keywords, start_date, end_date, max_results_per_keyword):
    papers = []
    keyword_totals = {keyword: 0 for keyword in keywords}  # Dictionary to store total papers found for each keyword
    
    # Convert start_date and end_date to datetime objects
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Split the date range into monthly intervals
    current_start_date = start_date
    date_ranges = []
    while current_start_date < end_date:
        current_end_date = current_start_date + timedelta(days=30)  # Approximate 1 month
        if current_end_date > end_date:
            current_end_date = end_date
        date_ranges.append((current_start_date.strftime("%Y-%m-%d"), current_end_date.strftime("%Y-%m-%d")))
        current_start_date = current_end_date + timedelta(days=1)
    
    # Use ThreadPoolExecutor to parallelize queries
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for keyword in keywords:
            for start, end in date_ranges:
                futures.append(executor.submit(fetch_papers_for_date_range, keyword, start, end, max_results_per_keyword))
        
        for future in as_completed(futures):
            papers.extend(future.result())
    
    # Count papers per keyword
    for paper in papers:
        keyword_totals[paper['keyword']] += 1
    
    # # print the total number of documents found for each keyword
    # print("\nTotal documents found per keyword:")
    # #for keyword, total in keyword_totals.items():
    #     print(f"{keyword}: {total} documents")
    
    return papers


def do_summary(api_key, keywords, start_date, end_date, max_results, output_path="result.txt"):
    global GEMINI_API_KEY
    GEMINI_API_KEY = api_key

    papers = fetch_papers(keywords, start_date, end_date, max_results)

    grouped = {}
    for paper in papers:
        grouped.setdefault(paper['keyword'], []).append(paper)

    html_output = "<html><body style='font-family:Arial, sans-serif;'>"
    html_output += f"<h2>Daily arXiv Summary for {start_date}</h2>"

    for keyword in sorted(grouped.keys()):
        html_output += f"<h3>{keyword.title()}</h3>"
        html_output += """
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th style="text-align: left;">Title</th>
                <th style="text-align: left;">Summary</th>
            </tr>
        """

        for paper in grouped[keyword]:
            abstract = paper['summary']
            if not abstract.startswith("Error"):
                summary = summarise_with_gemini(abstract)
            else:
                summary = "Error fetching abstract."
            title_link = f"<a href='{paper['link']}'>{paper['title']}</a>"
            html_output += f"<tr><td>{title_link}</td><td>{summary}</td></tr>"

            time.sleep(7)

        html_output += "</table><br>"

    html_output += "</body></html>"

    with open(output_path, "w") as f:
        f.write(html_output)

    return len(papers)
