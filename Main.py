import pyodbc
from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from re import sub
from decimal import Decimal

def get_url(url):
    """
    Pobiera HTML z URL
    :param url:
    :return:
    """
    try:
        print("Pobieram URL: {}".format(url))
        with closing(get(url,headers={
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
        }, stream=True)) as resp:
            if response_good(resp):
                print("URL Pobrany.")
                return resp.content
            else:
                print("URL nie został pobrany.")
                return None

    except RequestException as e:
        log_error('Error during request to {0} : {1}'.format(url, str(e)))
        return None

def response_good(resp):
    """
    If response is HTML = TRUE
    :param resp:
    :return:
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200
            and content_type is not None
            and content_type.find('html') > -1)

def log_error(e):
    print(e)

def offer_list(html, minPrice):
    """
    Appends offers above price limit to all_offers if they are not present in db_offers
    :param html: HTML file (parsed)
    :param minPrice: Offers minimum price to be added
    :return:
    """
    print("Tworzenie listy ofert do Bazy Danych...")
    tds = html.findAll("td", {"class": "offer"})

    for td in tds:

        title = td.find("td", {"class": "title-cell"}).text.strip()
        price = td.find("p", {"class": "price"}).text.strip()
        price = Decimal(sub(r'[^\d.]', '', price))
        link = td.find("a")
        location = td.findAll("small", {"class": "breadcrumb x-normal"})
        full_offer = [title, float(price), link['href'], location[1].text.strip()]
        if any(full_offer[2] in s for s in db_offers):
            print("Oferta jest już w bazie danych")
        elif full_offer[1] > float(minPrice):
            all_offers.append(full_offer)

    print("Lista została utworzona z wpisami w ilości {}.".format(len(all_offers)))

def get_db_links():
    """
    Returns actual db links to check for doubles
    :return: all actual offers from db in a list
    """
    print("Pobieranie aktualnej listy linków.")
    conn = pyodbc.connect('DRIVER={SQL Server};SERVER=den1.mssql8.gear.host;UID=olx;PWD=In5F_gvkm?q6')
    cursor = conn.cursor()
    cursor.execute("SELECT Link FROM garaze")
    results = []
    for row in cursor.fetchall():
        results.append(str(row))
    print("Lista linków została pobrana z wpisami w ilości {}.".format(len(results)))
    return results

def db_commit(table):
    """
    Commits rows from given list of lists
    :param table: all_offers table
    :return:
    """
    if len(table) != 0:
        print("Przesyłanie listy ofert do bazy danych...")
        conn = pyodbc.connect('DRIVER={SQL Server};SERVER=den1.mssql8.gear.host;UID=olx;PWD=In5F_gvkm?q6')
        cursor = conn.cursor()
        cursor.executemany("INSERT INTO garaze VALUES (?,?,?,?)", table)
        cursor.commit()
        print("Baza przesłana pomyślnie.")
    else:
        print("Lista do bazy danych jest pusta!")

def last_page(html):
    page_num = html.find("a", {"data-cy": "page-link-last"}).text.strip()
    return page_num

url = 'https://www.olx.pl/nieruchomosci/garaze-parkingi/sprzedaz/warszawa/'
raw_html = get_url(url)
html = BeautifulSoup(raw_html, 'html.parser')
page_num = int(last_page(html))
for i in range(page_num):
    url = 'https://www.olx.pl/nieruchomosci/garaze-parkingi/sprzedaz/warszawa/?page={}'.format(i+1)
    raw_html = get_url(url)
    html = BeautifulSoup(raw_html, 'html.parser')
    all_offers = []
    db_offers = get_db_links()
    offer_list(html, 15000)
    db_commit(all_offers)

