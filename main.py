import datetime
import json
import os
import pickle
import re
from pprint import pprint
from html.parser import HTMLParser
from pyvirtualdisplay import Display

from selenium import webdriver


def login(driver, credentials_filename):
    username_input = driver.find_element_by_id("username")
    password_input = driver.find_element_by_id("password")

    try:
        credentials = json.loads(open(credentials_filename).read())

        if 'username' not in credentials or 'password' not in credentials:
            raise Exception("Missing username or password")
    except Exception as e:
        print("Could not load credentials.json")
        print(e)
        return False

    username_input.send_keys(credentials['username'])
    password_input.send_keys(credentials['password'])

    submit_button = driver.find_element_by_class_name("submit")
    submit_button.click()

    if len(driver.find_elements_by_class_name("error-box")) > 0:
        print("Can't login because jExam sucks")
        return False
    return True


def get_link(driver, text, look_in="text"):
    links = driver.find_elements_by_tag_name("a")
    for link in links:
        if look_in == 'text' and text in link.text:
            return link
        elif look_in == 'html' and text in link.get_attribute("innerHTML"):
            return link


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_html_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def clean_column(text):
    if "cross.png" in text:
        text = "Nicht Bestanden"
    elif "tick.png" in text:
        text = "Bestanden"
    text = strip_html_tags(text)
    text = text.replace("\t", "").replace("\n", "")
    return text.strip()


def clean_row(row):
    return list(
        filter(lambda t: t != "" and t != "-",
               map(clean_column,
                   map(lambda c: c.get_attribute("innerHTML"),
                       row))))


def create_courses(rows: list) -> list:
    courses = []
    for row in rows:
        course = {'grade': []}
        for column in row:
            date_pattern = r'([0-9]{2}\.[0-9]{2}\.[0-9]{4})'
            date_match = re.match(date_pattern, column[:10])
            if date_match and date_match.group(1):
                course['date'] = datetime.datetime.strptime(column[:10], "%d.%m.%Y")
            if "INF" in column:
                course['name'] = column
            if "Bestanden" in column:
                if "Nicht" in column:
                    course['passed'] = False
                else:
                    course['passed'] = True
            try:
                num = float(column)
                course['grade'].append(num)
            except ValueError:
                pass

        if len(course) == 1 and len(course['grade']) == 0:
            continue
        if len(course['grade']) > 0:
            course['grade'] = course['grade'][-1]
        else:
            course['grade'] = 1.0
        courses.append(course)

    return courses


def check_for_differences(result_filename, new_courses):
    if os.path.exists(result_filename):
        with open(result_filename, "rb") as f:
            old_courses = pickle.load(f)

        global_found_diff = False

        for new_course in new_courses:
            old_course = None
            for old_course in old_courses:
                if old_course['name'] == new_course['name']:
                    break
                old_course = None

            if old_course is None:
                global_found_diff = True
                print("Found a new grade:")
                print("\t", new_course)
                continue

            found_diff = False
            for key in new_course:
                if old_course[key] != new_course[key]:
                    found_diff = True
                    break

            if found_diff:
                global_found_diff = True
                print("Found a difference:")
                print("\tOld:", old_course)
                print("\tNew:", new_course)

        if not global_found_diff:
            print("No new grades found.")


def main():
    virtual_display = Display(visible=0, size=(800, 600))
    virtual_display.start()

    credentials_filename = "credentials.json"
    if not os.path.exists(credentials_filename):
        print("Create a credentials.json file")
        return

    try:
        driver = webdriver.Chrome()
    except Exception as e:
        print(e)
        print("Could not initialize the webdriver")
        return

    driver.get("https://jexam.inf.tu-dresden.de/de.jexam.web.v4.5/spring/welcome")

    if not login(driver, credentials_filename):
        driver.close()
        return

    get_link(driver, "Ergebnisse abrufen").click()

    continue_button = driver.find_element_by_class_name("button")
    continue_button.click()

    get_link(driver, "plusplus0", "html").click()

    table = driver.find_element_by_tag_name("tbody")
    rows = table.find_elements_by_tag_name("tr")
    rows = list(
        map(clean_row,
            map(lambda x: x.find_elements_by_tag_name("td"),
                rows)))

    get_link(driver, 'Abmelden').click()
    driver.close()

    courses = create_courses(rows)

    #pprint(courses)

    result_filename = "last_result.bin"
    check_for_differences(result_filename, courses)

    with open(result_filename, "wb+") as f:
        pickle.dump(courses, f)


def alter_result():
    """
    Test method to see if different kinds of changes are being reported
    """
    result_filename = "last_result.bin"
    with open(result_filename, "rb") as f:
        last_courses = pickle.load(f)

    last_courses[0]['grade'] = 5.0
    last_courses = last_courses[:-1]

    with open(result_filename, "wb+") as f:
        pickle.dump(last_courses, f)


if __name__ == '__main__':
    main()
