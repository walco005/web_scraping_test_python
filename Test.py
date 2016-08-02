"""This program scrapes information from the Arkansas Medical Board website
for a given search query and returns the doctors information as a CSV file."""

import urllib2
import time
import csv
from collections import OrderedDict
from selenium import webdriver
from bs4 import BeautifulSoup

FILE_NAME = "results.csv"
PREFIX_URL = "http://www.armedicalboard.org/public/verify/"
PHANTOMJS_PATH = "C:\\Python27\\phantomjs-2.1.1-windows\\bin\\phantomjs.exe"
SPAN_ID = "ctl00_ctl00_MainContentPlaceHolder_innercontent_"
BROWSER = webdriver.PhantomJS(executable_path=PHANTOMJS_PATH)


def last_name_search(query):
    """Searches through the Arkansas Medical Board website for doctors
    by last name.

    Args:
        query: The substring of a last name you wish to search by.

    Returns:
        A list of dicts containing information from doctors in this format:
        {"name": a, "city": b, "state": c, "zip": d, "license num": e,
         "expiration date": f, "status": g}
        If a doctor has multiple licenses listed it will return each license
        in a different dict.
    """
    search_method = "LName"
    BROWSER.get("http://www.armedicalboard.org/public/verify/lookup.aspx?" +
                search_method + "=" + query)
    link_list = get_links(1)
    unique_url_list = list(OrderedDict.fromkeys(link_list))
    print "%d unique doctors found." % len(unique_url_list)
    doctor_list = []
    i = 0
    for link in unique_url_list:
        if i % 10 == 0:
            print "%d of %d doctors scraped..." % (i, len(unique_url_list))
        time.sleep(0.5)
        doctor_list.extend(scrape_info(link))
        i += 1
    print "%d licenses from %d doctors scraped." % (len(doctor_list), i)
    return doctor_list

def lic_num_search(query):
    """Searches through the Arkansas Medical Board website for a doctor
    with a given license number. It prints a dict containing the doctors
    information along with information pertaining to their specified license.

    Args:
        query: The license number the user wishes to search by.
    """
    search_method = "LicNum"
    BROWSER.get("http://www.armedicalboard.org/public/verify/lookup.aspx?" +
                search_method + "=" + query)
    time.sleep(0.5)
    doctor = scrape_info(BROWSER.current_url, query)
    print doctor

def get_links(current_page, url_list=[]):
    """Recursively gets all of the urls from the search result pages.

    get_links uses a browser that is at the first page of a table of search
    results and goes through all of them, grabbing every link in the table
    and returning a list of them as strings.

    Args:
        current_page: The page that get_links is starting from.

    Returns:
        url_list: a list containing all the urls found so far, then at the end
        returns the entire list of urls received.
    """
    results_page = BeautifulSoup(BROWSER.page_source, "html.parser")
    last_link = results_page.find("table").find_all("a", href=True)[-1].text
    if current_page % 10 == 1:
        if "..." == last_link:
            counter = 1
            while counter <= 10:
                time.sleep(0.5)
                url_list.extend(get_urls_from_page())
                current_page += 1
                next_page(current_page)
                counter += 1
            get_links(current_page)
        elif last_link.isdigit():
            last_page = int(last_link)
            while current_page <= last_page:
                time.sleep(0.5)
                url_list.extend(get_urls_from_page())
                current_page += 1
                next_page(current_page)
        elif "select" == last_link:
            url_list.extend(get_urls_from_page())
    return url_list

def get_urls_from_page():
    """Takes a search results page and returns a list of all the links to
    doctors web pages.

    Returns:
        A list of all the urls on the current page that lead to a doctors
        web page.
    """
    link_list = []
    soup = BeautifulSoup(BROWSER.page_source, "html.parser")
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and "results" in href:
            url = PREFIX_URL + href
            link_list.append(url)
    return link_list

def scrape_info(url, query=""):
    """Scrapes a web page for information on a doctor.

    This function scrapes information on a doctor and has two outcomes:
     1. If it's a last name search, it grabs information on the doctor and
     their licenses, returning them as a list of dicts, each dict is for
     a different license the doctor has.
     2. If it's a license number search, it grabs the information on the
     doctor and the information on that specific license, returning a single
     dict.

    Args:
        url: The url of the web page that will be scraped.
        query: Used only in license number searches, this specifies which
        license is being searched for.
    Returns:
        doc_list: A list containing dicts of each license the doctor has.
        (Used in last name search)
        tmp_doc: A dict containing the license specified in query.
        (Used in license number search)
    """
    doc_list = []
    page = urllib2.urlopen(url)
    doctor_page = BeautifulSoup(page.read(), "html.parser")

    if doctor_page.find(title="Error on page"):
        print "Doctor could not be returned because of error on webpage: ", url
        return doc_list

    name = doctor_page.find(id=SPAN_ID + "ListView1_ctrl0_Label1").text
    print name
    if not doctor_page.find(text="No data was returned"):
        city = doctor_page.find(id=SPAN_ID + "ListView2_ctrl0_Label3").text
        state = doctor_page.find(id=SPAN_ID + "ListView2_ctrl0_Label4").text
        zip_code = doctor_page.find(id=SPAN_ID + "ListView2_ctrl0_Label5").text

    if query:
        # License Number Search
        span = doctor_page.find(text=query).parent
        amount = str(span)[72:73]
        lic_num = query
        exp_date = doctor_page.find(id=SPAN_ID + "ListView3_ctrl%s_Label3"
                                                 % amount).text
        status = doctor_page.find(id=SPAN_ID + "ListView3_ctrl%s_Label5"
                                               % amount).text
        tmp_doc = {"name": name, "city": city, "state": state,
                   "zip": zip_code, "license num": lic_num,
                   "expiration date": exp_date, "status": status}
        return tmp_doc
    else:
        # Last Name Search
        i = 0
        while doctor_page.find(id=SPAN_ID + "ListView3_ctrl%d_Label1" % i):
            lic_num = doctor_page.find(id=SPAN_ID +
                                       "ListView3_ctrl%d_Label1" % i).text
            exp_date = doctor_page.find(id=SPAN_ID +
                                        "ListView3_ctrl%d_Label3" % i).text
            status = doctor_page.find(id=SPAN_ID +
                                      "ListView3_ctrl%d_Label5" % i).text
            tmp_doc = {"name": name, "city": city, "state": state,
                       "zip": zip_code, "license num": lic_num,
                       "expiration date": exp_date, "status": status}
            doc_list.append(tmp_doc)
            i += 1
        return doc_list


def next_page(page_num):
    """Continues to the given page in the search result table."""
    js_string = "javascript:__doPostBack('ctl00$ctl00$MainContentPlaceHolder" \
                "$innercontent$gvLookup','Page$%d')" % page_num
    BROWSER.execute_script(js_string)

def print_csv(doctor_list):
    """Prints a list of dictionaries containing doctors information to a
    CSV file."""
    with open(FILE_NAME, "wb") as csvfile:
        fieldnames = ["name", "city", "state", "zip", "license num",
                      "expiration date", "status"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for doctor in doctor_list:
            writer.writerow(doctor)


if __name__ == "__main__":
    method_number = int(raw_input("Search by (1) Last Name "
                                  "or (2) License Number? "))
    if method_number == 1:
        query = raw_input("Last name substring you wish to search by: ")
        doc_list = last_name_search(query)
        print_csv(doc_list)
        print "%d results printed to %s" % (len(doc_list), FILE_NAME)
    elif method_number == 2:
        query = raw_input("License number you wish to search by: ")
        lic_num_search(query)
    BROWSER.close()
