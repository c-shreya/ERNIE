"""
Title: Email Parser-Downloader-Tester
Author: Djamil Lakhdar-Hamina
Date: 06/24/2019


The point of this parser is to take an email and scan it for url.
Once the url is found it opens it up and saves it to a specified directory.
This is code for an automated process which will leverage Jenkins to set off a process when
triggered by the reception of an email with a url-link.

Example link:

https://sccontent-scudd-delivery-prod.s3.amazonaws.com/sccontent-scudd-delivery-prod/nete_1557815293641/2019-6-4/nete_1557815293641_2019-6-4_ANI-ITEM-delete.zip?AWSAccessKeyId=AKIA33DQTS4C4RTMKWFE&Expires=1567427254&Signature=Lecw433oI7gWk4jqVwO8B3KsH%2BY%3D


"""
import re
import zipfile
import webbrowser
from sys import argv
import time

start_time=time.time()

##Build a function that 1) opens email 2) scans it for urls 3) stores urls and then opens file in them 4) then rename this downloaded file and store in specified directory.

pmt_content=argv[1]
#directory= argv[2]

def email_parser(pmt_content):
    """
    Assumptions:

    Given an email, read the email, then scan it for url.
    If url is found, download, rename, and then save to specified directory.

    Arguments: email_message and default directory= /Scopus

    Input: email_message with forwarded emails called pmt_content because that is the property name given by Jenkins when you call as variable to be executed in process
    Output: A group of zip files, renamed, and stored in specified directory called /Scopus

    :return:
    """

    links= re.findall('https://\S*.3D',pmt_content)
    links.remove(links[1])
    for link in links:
    ## Go through list of links, rename
        url_request = webbrowser.open(link)
        scopus_update_zip_file = zipfile.ZipFile(url_request)
        # scopus_update_zip_file.filename = link[0].split('/')[2]
        ## Now store them in specified directory
        ## os.path.join(directory, scopus_update_zip_file)

## Run the function with the relevant input
scopus_zip_files=email_parser(pmt_content)
print('The revelevant zip files are:', scopus_zip_files)
print('Total duration ',time.time()-start_time)
## End of the script
