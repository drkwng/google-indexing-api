import re
import json
import csv

import httplib2
from oauth2client.service_account import ServiceAccountCredentials


class GoogleIndexationAPI:
    def __init__(self, key_file, urls_list):
        """
        :param key_file: .json key Google API filename
        :type key_file:
        :param urls_list: .txt urls list filename
        :type urls_list:
        """
        self.key_file = key_file
        self.urls_list = urls_list

    @staticmethod
    def choose_mode():
        """
        Choosing a mode: SAFE (1 domain processing) or SAFE (multi-domain processing)
        :return method: method name
        """
        while True:
            choose_msg = input('Choose one of modes and press Enter \n'
                               '1 - SAFE MODE (1 domain processing)\n'
                               '2 - PRO MODE (multi-domain processing)\n')
            if choose_msg not in ['1', '2']:
                print('Please enter correct number')

            else:
                print('You chose mode: ', choose_msg)
                return choose_msg

    @staticmethod
    def get_domain():
        """
        Input URL and strips it to a domain name (only in safe mode)
        :return stripped_domain:
        """
        domain = input('Enter domain you are going to work with: ')
        stripped_domain = re.sub(r'(https?://)|(www.)|/(.*)', '', domain)
        print(stripped_domain)
        return stripped_domain

    @staticmethod
    def choose_method():
        """
        Choosing a method for Google Indexing API request
        :return method: method name
        """
        while True:
            choose_msg = input('\nChoose one of methods (print number) and press Enter \n'
                               '1 - URL_UPDATED\n'
                               '2 - URL_DELETED:\n')
            if '1' in choose_msg:
                method = 'URL_UPDATED'
                break
            elif '2' in choose_msg:
                method = 'URL_DELETED'
                break
            else:
                print('Please enter correct number')

        print('You chose method: ', method)
        return method

    @staticmethod
    def get_domains(urls):
        """
        Get domains from URLs
        :param urls: all urls from file
        :type urls: list
        :return _domains:
        """
        domains = set()
        for url in urls:
            domain = re.sub(r'(.*://)?([^/?]+).*', r'\1\2', url)
            domains.add(domain)
        return domains

    def get_urls(self, mode):
        """
        Gets URL list from a file and clean from not unique and not valid data
        :param mode: Selected by user mode
        :type mode: str
        :return final_urls:
        """
        urls = []
        if mode == '1':
            domain = self.get_domain()
        else:
            domain = 'No Domain. You chose a PRO mode!'
        try:
            with open(self.urls_list, 'r', encoding='utf-8') as f:
                for line in f:
                    urls.append(line.strip())

                # Clean not unique urs
                domains = self.get_domains(urls)
                # Delete urls without ^http or which don't contain our domain name
                if mode == '2':
                    urls = [u for u in set(urls)
                            if u.startswith('http')]
                elif mode == '1':
                    urls = [u for u in set(urls)
                            if u.startswith('http') and domain in u]

                # 200 requests a day quota :(
                if len(urls) > 200:
                    print(f'You have a 200 request per day quota. You are trying to index {len(urls)}. ')

                    len_answer = input(f'I will make requests only for the first 200 urls. '
                                       f'Continue (YES/NO) ???\n')
                    if 'yes' in len_answer.lower():
                        final_urls = urls[0:199]
                        left_urls = urls[200:]

                        # Write urls over quota limit in file
                        with open('not_send_urls.txt', 'w', encoding='utf-8') as log:
                            for item in left_urls:
                                log.write(f'{item}\n')
                        print(f'There are {len(left_urls)} not send to Googlebot. \n'
                              f'Check not_send_urls.txt file in the script folder')

                    elif 'no' in len_answer.lower():
                        exit()
                    else:
                        print('Please enter correct answer (YES / NO)')
                else:
                    final_urls = urls

                if len(final_urls) < 1:
                    assert print('There are no urls in your file')
                    exit()

                return final_urls, domains

        except Exception as e:
            print(e, type(e))
            exit()

    def parse_json_key(self, domains, mode):
        """
        Parses and validates JSON.
        Prints information about domains and Google Search Console rights for API service account.
        :param domains: Domains from URLs
        :type domains: set
        :param mode: Selected by user mode
        :type mode: str
        """
        with open(self.key_file, 'r') as f:
            key_data = json.load(f)
            if mode == '2':
                print('\nYour domains: ', domains)
            input(f'\nPlease add OWNER rights in GSC resource(s) to: {key_data["client_email"]} \nand press Enter')

    def single_request_index(self, url, method):
        """
        Makes a request to Google Indexing API with a selected method
        :param url: URL
        :type url: str
        :param method: Selected by user mode
        :type method: str
        :return content: Response from API
        """
        api_scopes = ["https://www.googleapis.com/auth/indexing"]
        api_endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.key_file, scopes=api_scopes)

        try:
            http = credentials.authorize(httplib2.Http())
            r_content = """{""" + f"'url': '{url}', 'type': '{method}'" + """}"""
            response, content = http.request(api_endpoint, method="POST", body=r_content)
            log = [url, method, response.status, content]
            return log

        except Exception as e:
            print(e, type(e))

    @staticmethod
    def parse_response(content):
        """
        Parses error response
        :param content: Error API response
        :type content: bytes
        :return result: parsed API response
        :rtype result: list
        """
        try:
            json_line = json.loads(content)
            result = [json_line['error']['message'], json_line['error']['status']]
        except Exception as e:
            result = ['API response parse error', e]
        return result

    def indexation_worker(self):
        """
        Run this method after class instance creating.
        Gets an URL list, parses JSON key file, chooses API method,
        then sends a request for an each URL and logs responses.
        """
        mode = self.choose_mode()
        urls, domains = self.get_urls(mode)
        self.parse_json_key(domains, mode)
        method = self.choose_method()
        print('Processing... Please wait')
        with open('logs.csv', 'w', encoding='utf-8', newline='') as f:
            my_csv = csv.writer(f, delimiter='\t')
            header = ['URL', 'METHOD', 'STATUS_CODE', 'ERROR_MESSAGE', 'ERROR_STATUS']
            my_csv.writerow(header)
            for url in urls:
                result = self.single_request_index(url, method)
                log = result[0:3]
                if result[2] != 200:
                    log.extend(self.parse_response(result[3]))
                my_csv.writerow(log)

        print(f"\nDone! We've sent {len(urls)} URLs to Googlebot. \nYou can check responses in logs.csv")


if __name__ == '__main__':
    g_index = GoogleIndexationAPI('cred.json', 'urls.txt')
    g_index.indexation_worker()
