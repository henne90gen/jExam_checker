import json
from selenium import webdriver


def get_link(driver, text, look_in="text"):
    links = driver.find_elements_by_tag_name("a")
    for link in links:
        if look_in == 'text' and text in link.text:
            return link
        elif look_in == 'html' and text in link.get_attribute("innerHTML"):
            return link


def main():
    credentials = json.loads(open("credentials.json").read())

    driver = webdriver.Chrome()
    driver.get("https://jexam.inf.tu-dresden.de/de.jexam.web.v4.5/spring/welcome")

    username_input = driver.find_element_by_id("username")
    password_input = driver.find_element_by_id("password")

    username_input.send_keys(credentials['username'])
    password_input.send_keys(credentials['password'])

    submit_button = driver.find_element_by_class_name("submit")
    submit_button.click()

    get_link(driver, "Ergebnisse abrufen").click()

    continue_button = driver.find_element_by_class_name("button")
    continue_button.click()

    get_link(driver, "plusplus0", "html").click()

    table = driver.find_element_by_tag_name("tbody")
    rows = table.find_elements_by_tag_name("tr")

    print(len(rows))


def strip_page():
    with open("page_source.html", "r") as f:
        source = f.read()
    lines = source.replace("\t", "").split("\n")
    lines = list(filter(lambda x: x.strip() != "", lines))
    for line in lines:
        print(line)
    print(lines)


if __name__ == '__main__':
    # strip_page()
    main()