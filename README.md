# Google Indexing API (Read before starting)

Made on Python 3.8.x

1. Go to https://console.cloud.google.com/ -> APIs & Services -> Credentials
2. Click "Create Credentials" -> "Service account" (Role - Owner, no domain app or other personal data needed).
3. Upload your service account JSON key to the folder with a python program and name it "cred.json".
4. Create "urls.txt" file in the folder with a python program. Put URLs to index in it (1 URL = 1 line).
5. Start the program and follow instructions in the console.

UPDATE: Use PRO mode after starting program to send different URLs with different domains.

Don't forget to install oauth2client. Enter in cmd:

`pip install oauth2client`

!!! Only 200 requests per day (Google API Indexing quota/account). Create more accounts to send more URLs🙊 
The program saves API response content into .csv file and URLs over 200 quotas into .txt file.

I appreciate your bug reports and suggestions🖖
