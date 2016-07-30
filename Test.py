"""This program scrapes information from the Arkansas Medical Board website
for a given search query and returns the doctors information as a CSV file."""
#TODO: Redo all the docstrings to adhere to Google Style Guide setup.
#https://google.github.io/styleguide/pyguide.html?showone=Comments#Comments
import urllib2
import time
from collections import OrderedDict
from selenium import webdriver
from bs4 import BeautifulSoup


PREFIX_URL = "http://www.armedicalboard.org/public/verify/"
PHANTOMJS_PATH = "C:\\Python27\\phantomjs-2.1.1-windows\\bin\\phantomjs.exe"
SPAN_ID = "ctl00_ctl00_MainContentPlaceHolder_innercontent_"
BROWSER = webdriver.PhantomJS(executable_path=PHANTOMJS_PATH)


class Doctor(object):
    """The Doctor object stores and returns relevant information
    about a doctor."""

    def __init__(self):
        self.name = ""
        self.city = ""
        self.state = ""
        self.zip_code = ""
        self.mailing_address = ""
        self.lic_num = ""
        self.exp_date = ""
        self.status = ""
        self.amount = 0

    def set_all_attr(self, name, city, state, zip_code, mailing_address,
                     lic_num, exp_date, status):
        """Sets all the relevant attributes of a Doctor."""
        self.name = name
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.mailing_address = mailing_address
        self.lic_num = lic_num
        self.exp_date = exp_date
        self.status = status

    def print_doctor(self):
        """Prints the doctor's information in a list form"""
        print "[Name:", self.name, ", City:", self.city, ", State:", \
            self.state, ", Zip:", self.zip_code, ", License Num:", \
            self.lic_num, ", Exp. Date:", self.exp_date, ", Status:",\
            self.status, "]"

def recursive_parse(current_page, url_list = []):
    """Gets all of the urls from the search result pages and returns
    a list of all the unique urls found."""
    results_page = BeautifulSoup(BROWSER.page_source, "html.parser")
    last_link = results_page.find("table").find_all("a", href=True)[-1].text
    if current_page % 10 == 1:
        if "..." in last_link:
            counter = 1
            while counter <= 10:
                time.sleep(0.5)
                url_list.extend(parse_results())
                current_page += 1
                print "Going to page %d" % current_page
                next_page(current_page)
            recursive_parse(current_page)
        elif last_link.isdigit():
            last_page = int(last_link)
            while current_page <= last_page:
                time.sleep(0.5)
                url_list.extend(parse_results())
                current_page += 1
                print "Going to page %d" % current_page
                next_page(current_page)
        elif "select" in last_link:
            url_list.extend(parse_results())
    unique_url_list = list(OrderedDict.fromkeys(url_list))
    return unique_url_list

def parse_results():
    """Returns a list containing all the urls that lead to a
    doctor's page in a search result page."""
    link_list = []
    soup = BeautifulSoup(BROWSER.page_source, "html.parser")
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and "results" in href:
            url = PREFIX_URL + href
            link_list.append(url)
    return link_list



def scrape_info(url, query=""):
    """Scrapes the doctors information from the given URL. Query is given only
    for license number searches."""
    page = urllib2.urlopen(url)
    doctor_page = BeautifulSoup(page.read(), "html.parser")
    tmp_doc = Doctor()

    if doctor_page.find(title="Error on page"):
        print "Doctor could not be returned because of error on webpage: ", url
        return 0

    name = doctor_page.find(id=SPAN_ID + "ListView1_ctrl0_Label1").text
    if not doctor_page.find(text="No data was returned"):
        city = doctor_page.find(id=SPAN_ID + "ListView2_ctrl0_Label3").text
        state = doctor_page.find(id=SPAN_ID + "ListView2_ctrl0_Label4").text
        zip_code = doctor_page.find(id=SPAN_ID + "ListView2_ctrl0_Label4").text
        mailing_address = doctor_page.find(id=SPAN_ID +
                                           "ListView2_ctrl0_Label1").text

    if not query: # Last Name Search
        # TODO: Implement amount to be used for finding the correct license
        lic_num = doctor_page.find(id=SPAN_ID + "ListView3_ctrl%d_Label1"
                                   % tmp_doc.amount).text
        exp_date = doctor_page.find(id=SPAN_ID + "ListView3_ctrl%d_Label3"
                                    % tmp_doc.amount).text
        status = doctor_page.find(id=SPAN_ID + "ListView3_ctrl%d_Label5"
                                  % tmp_doc.amount).text
        tmp_doc.amount += 1
    else: # License Number Search - COMPLETED
        span = doctor_page.find(text=query).parent
        amount = str(span)[72:73]
        lic_num = query
        exp_date = doctor_page.find(id=SPAN_ID + "ListView3_ctrl%s_Label3"
                                    % amount).text
        status = doctor_page.find(id=SPAN_ID + "ListView3_ctrl%s_Label5"
                                  % amount).text

    tmp_doc.set_all_attr(name, city, state, zip_code, mailing_address, lic_num,
                         exp_date, status)
    tmp_doc.print_doctor()

def next_page(page_num):
    """Continues to the given page in the search result table."""
    js_string = "javascript:__doPostBack('ctl00$ctl00$MainContentPlaceHolder" \
                "$innercontent$gvLookup','Page$%d')" % page_num
    BROWSER.execute_script(js_string)

if __name__ == "__main__":
    search_method = ""
    query = ""
    s_method_number = raw_input("Search by (1) Last Name "
                                "or (2) License Number? ")
    s_method_number = int(s_method_number)

    if s_method_number == 1:
        search_method = "LName"
        query = raw_input("Last name substring you wish to search by: ")
    elif s_method_number == 2:
        search_method = "LicNum"
        query = raw_input("License number you wish to search by: ")
    BROWSER.get("http://www.armedicalboard.org/public/verify/lookup.aspx?" +
                    search_method + "=" + query)
    if s_method_number == 2:
        time.sleep(0.5)
        scrape_info(BROWSER.current_url, query)
    link_list = recursive_parse(1)
    for link in link_list:
        print link
    BROWSER.close()