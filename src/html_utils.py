from bs4 import BeautifulSoup
import markdownify
import requests


def extract_url_title_time(soup):
    url = ""
    title = ""
    revised_time = ""
    tables = []
    try:
        if soup.find("title"):
            title = str(soup.find("title").string)

        og_url_meta = soup.find("meta", property="og:url")
        if og_url_meta:
            url = og_url_meta.get("content", "")

        for table in soup.find_all("table"):
            tables.append(markdownify.markdownify(str(table)))
            table.decompose()

        text_content = soup.get_text(separator=" ", strip=True)
        text_content = " ".join(text_content.split())

        return url, title, text_content, tables
    except:
        print("parse error")
        return "", "", "", "", []


def extract_html_content(df):
    """
    Columns in df: "url", "quarter", "year"
    """

    urls = list(df["url"].to_list())

    urls_content = []
    for url in urls:
        urls_content.append(requests.get(url).content)

    parsed_htmls = []
    for url_content in urls_content:
        soup = BeautifulSoup(url_content, "html.parser")
        url, title, content, tables = extract_url_title_time(soup)
        parsed_htmls.append(
            {"url": url, "title": title, "content": content, "tables": tables}
        )
    return parsed_htmls
