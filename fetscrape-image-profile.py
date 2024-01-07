import requests
from bs4 import BeautifulSoup
import time
from fake_useragent import UserAgent
import random
import json
import html
import os
import re


def random_sleep():
    time.sleep(random.uniform(5, 10))


def sanitize_filename(filename):
    if filename is None:
        return
    # Define a regular expression pattern to match invalid characters
    invalid_chars_pattern = re.compile(r'[\\/:"*?<>|�\r\n]')
    # Replace invalid characters with underscores
    sanitized_filename = re.sub(invalid_chars_pattern, '', filename)

    return sanitized_filename[:220].strip()


def get_image_and_download(simplified_obj, headers, base_url, folder_path, session: requests.Session):
    for o in simplified_obj:
        url = "https://fetlife.com" + o['permalink']

        new_headers = {**headers, 'Referer': base_url}

        response = session.get(url, headers=new_headers)
        soup2 = BeautifulSoup(response.content, 'lxml')

        pic_json = soup2.find('script', {'id': 'story-data'}).text
        pic_data = json.loads(pic_json)

        double_xl = pic_data['attributes']['pictures'][0]['src2x']

        new_headers_v2 = {**headers, 'Referer': url}
        img_r = session.get(double_xl, headers=new_headers_v2)

        content_type = img_r.headers.get('Content-Type')

        if content_type.startswith("image/"):
            filename = f"{folder_path}/{sanitize_filename(o['caption'])}.jpg"

            # Save the response content to a file
            with open(filename, "wb") as file:
                file.write(img_r.content)

            print(f"Image saved as '{filename}'.")
            time.sleep(random.uniform(3, 5))
        else:
            print(f"Unexpected content type: {content_type}")


def main(username, password, url, directory):
    ua = UserAgent()
    headers = {'User-Agent': ua.chrome}

    # login#
    login_data = {
        'user[login]': username,
        'user[password]': password,
        'user[locale]': 'en',
        'user[otp_attempt]': 'step_1',
        'utf8': '✓'
    }

    with requests.Session() as s:
        login_url = 'https://fetlife.com/login'
        r = s.get(login_url, headers=headers)
        print(r)
        soup = BeautifulSoup(r.content, 'lxml')
        login_data['authenticity_token'] = soup.find('input', attrs={'name': 'authenticity_token'})['value']
        r = s.post(login_url, data=login_data, headers=headers)

    # target definition#
    base_url = url + '/pictures'
    print(base_url)
    r2 = s.get(base_url, headers=headers)
    soup = BeautifulSoup(r2.content, 'lxml')

    print(soup.select('title')[0].text)
    name_probably = soup.select('title')[0].text.split(' | ')[0].split('of ')[1]

    folder_path = f"{directory}/{name_probably}"
    print(folder_path)
    os.makedirs(folder_path, exist_ok=True)

    div_element = soup.find('div', {'data-component': 'PicturesGallery'})

    if div_element:
        data_props_value = div_element.get('data-props')
        decoded_value = html.unescape(data_props_value)

        data = json.loads(decoded_value)
        entries = data['preload']['entries']
        simplified_obj = [{
            "permalink": obj["permalink"],
            "caption": obj["caption"],
            "nickname": obj["nickname"]
        } for obj in entries]

        get_image_and_download(simplified_obj, headers, base_url, folder_path, s)

        if len(simplified_obj) >= 29:
            time.sleep(2)
            new_headers = {**headers, 'Referer': base_url, 'Accept': 'application/json'}

            index = 2;
            while True:
                print(f"Getting images from page {index}")
                scroll_url = base_url + f"?responsive=true&page={index}&order=newest&filter=all"
                more_pics = s.get(scroll_url, headers=new_headers)

                data = json.loads(more_pics.content)
                entries = data['entries']

                if len(entries) == 0:
                    break

                simplified_obj_more = [{
                    "permalink": obj["permalink"],
                    "caption": obj["caption"],
                    "nickname": obj["nickname"]
                } for obj in entries]
                get_image_and_download(simplified_obj_more, headers, base_url, folder_path, s)
                index += 1

    else:
        print('No matching div element found')

    print('Completed page ' + name_probably)

if __name__ == '__main__':
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"

    directory = input(YELLOW + "Enter the directory path to save images: (Press ENTER to use current directory): " + RESET)
    if directory == '':
        directory = os.getcwd()


    # keep asking for url until valid
    while True:
        url = input(YELLOW + "Enter the FetLife URL: " + RESET)

        if url != '' and url.startswith('https://fetlife.com/users/'):
            print(GREEN + 'URL looks good' + RESET)

            pattern = r"(https://fetlife\.com/users/\d+)(?:/pictures)?"

            match = re.match(pattern, url)

            if match:
                url = match.group(1)
                break        
        print(RED + 'URL is not valid, please try again. Must be of the form https://fetlife.com/users/<user_id>' + RESET)

    username = input(YELLOW + "Enter your FetLife username: " + RESET)
    password = input(YELLOW + "Enter your FetLife password: " + RESET)

    print(GREEN + 'Starting FetLife Image Profile Scraper' + RESET)

    main(username, password, url, directory)