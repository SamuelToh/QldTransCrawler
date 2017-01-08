from StringIO import StringIO 
import os, re, pycurl, smtplib, time, datetime
from HTMLParser import HTMLParser

test_dates_cache = dict()
test_dates_to_send = []

# TO BE CONFIGURED
WANT_MONTH = 1
WANT_DAY_LESS = 30 
jsessionId = "YOUR_SESSION_ID_HERE"
gmail_addr = "YOUR GMAIL ADDRESS"
gmail_app_token = "YOUR APPLICATION TOKEN"
nominated_email_addr = []

TIMEOUT_MESSAGE = "Your browser may have timed out."

PART_TEST_DATE_TIME_POSITION = 0
PART_TEST_DATE_POSITION = 3

class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        # print "Encountered a start tag:", tag.lstrip().rstrip()
        return 1

    def handle_endtag(self, tag):
        # print "Encountered an end tag :", tag.lstrip().rstrip()
        return 1

    def handle_data(self, data):
        processed_data = data.lstrip().rstrip()
        # print "Encountered some data  :", processed_data
        if TIMEOUT_MESSAGE in processed_data:
            raise Exception('JSESSION Key has timed out. PLease request for a new one before running again...')

        if "Sherwood" in processed_data:
        	self.handle_testdates(processed_data)


    def handle_testdates(self, data):
        verbose("    * Test dates: " + data)
        parts = data.split()
        test_date_key = parts[PART_TEST_DATE_POSITION] + " " + parts[PART_TEST_DATE_TIME_POSITION]

        d = datetime.datetime.strptime(parts[PART_TEST_DATE_POSITION], "%d/%m/%Y")

        if d.month == WANT_MONTH and d.day < WANT_DAY_LESS:
            # Is a month the script is after and the day is less than what the script specified!
            if test_date_key not in test_dates_cache:
                # And is not in the cache, not reported yet
                test_dates_cache[test_date_key] = True
                test_dates_to_send.append(test_date_key)
                verbose("    *--> Found potential test date on " + test_date_key)


# Setup details
parser = MyHTMLParser()
server = smtplib.SMTP('smtp.gmail.com', 587)

qld_transport_url = "https://www.service.transport.qld.gov.au/SBSExternal/FormRequestReceiverServlet/"
post_data = "formName=BookingSearchCriteria&fieldName=&fieldValue=&UI_Event=SUBMIT&dialogName=Booking&applicationGroupName=SBSExternal&applicationName=sbsexternal&executionContext=qt&requestURI=%2FSBSExternal%2FBookingSearch.jsp&productGroup=DE&firstRender=N&region=21387484948500&centre=96000000&nextAvailableBooking=Next+available+booking+or&buttonRowGridSelectedRow=-1&buttonRowGridSelectedColumn=-1&bodyGridSelectedRow=-1&bodyGridSelectedColumn=-1&layoutGridSelectedRow=-1&layoutGridSelectedColumn=-1"


def verbose(msg):
	print str(time.time()) + "] " + msg

def poll_sherwood():
    verbose("  -> Polling the Qld transport page for test date...")
    storage = StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, qld_transport_url)
    c.setopt(pycurl.FOLLOWLOCATION, True)
    c.setopt(c.WRITEFUNCTION, storage.write)
    c.setopt(pycurl.HTTPHEADER, [
      'Cookie: _ga=GA1.4.389744457.1483482602; LPVID=M0YjRiZjA1ZjBjYzdhNGZj; LPSID-36317183=WEUbG0HOSJOMK0i66CrkrQ.fbb1b3b5808a3139e405467b664bce06d8268b0c; __utma=256087945.389744457.1483482602.1483482603.1483482603.1; __utmc=256087945; __utmz=256087945.1483482603.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _gat_UA-7276966-11=1; JSESSIONID=' + jsessionId + '; _ga=GA1.5.389744457.1483482602',
      'Origin: https://www.service.transport.qld.gov.au',
      'Accept-Encoding: application/json, deflate',
      'Accept-Language: en-GB,en-US;q=0.8,en;q=0.6',
      'Upgrade-Insecure-Requests: 1',
      'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.73 Safari/537.36',
      'Content-Type: application/x-www-form-urlencoded',
      'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      'Cache-Control: max-age=0',
      'Referer: https://www.service.transport.qld.gov.au/SBSExternal/BookingSearch.jsp',
      'Connection: keep-alive'])
    c.setopt(c.POSTFIELDS, post_data)
    c.perform()
    c.close()
    return storage.getvalue()

def parse_data(data):
    parser.feed(data)

def send_email():
    global test_dates_to_send 
    if len(test_dates_to_send) > 0:
        verbose("Sending new test dates to email...")
        server.starttls()
        server.login(gmail_addr, gmail_app_token)

        content = "New test dates = \n" + '\n'.join(map(str, test_dates_to_send))
 
        msg = 'Subject: %s\n\n%s' % ('New test date for Sherwood driving center found!', content)
        verbose("Email message is => " + msg)
        server.sendmail(gmail_addr, nominated_email_addr, msg)
        server.quit()
        test_dates_to_send = []


def main():
    verbose("Starting Sam's polling script...")
    while (1):
        parse_data(poll_sherwood())
        send_email()
        verbose("Next poll in 60 seconds...")
        time.sleep(60)


if __name__ == '__main__':
    main()
