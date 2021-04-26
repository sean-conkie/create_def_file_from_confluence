import datetime
import sys
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, WebDriverException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from winreg import *

def __addoptions__(opts,headless=True):

    opts.headless = headless
    opts.add_argument("--log-level=3")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--remote-debugging-port=9222")
    if headless:
        assert opts.headless  # Operating in headless mode
    return opts

def __logger__(msg):
    print(f'{datetime.datetime.now():%Y-%m-%d %H:%M:%S}: {msg}')

def __prettifydict__(d):
    outp = ['  {\n']
    for i, k in enumerate(d.keys()):
        if i > 0:
            outp.append(',\n')
        if isinstance(d[k],dict):
            outp.append(f'    "{k:}":{__prettifydict__(d[k]):}')
        elif isinstance(d[k],list):
            outp.append(f'    [\n')
            for j,l in enumerate(d[k]):
                if j > 0:
                    outp.append(',\n')
                outp.append(f'      "{l:}"')
            outp.append(f'\n    ]')
        else: 
            outp.append(f'    "{k:}": "{d[k]:}"')

    outp.append('\n  }')
    return ''.join(outp)

def createdef(url,email=None,headless=True):
    # start driver
    try:
        with OpenKey(HKEY_CURRENT_USER, r'Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations\\http\\UserChoice') as key:
            browser = QueryValueEx(key, 'Progid')[0]

        if browser == 'ChromeHTML':
            opts = webdriver.chrome.options.Options()
            opts = __addoptions__(opts,headless)
            driver = webdriver.Chrome(executable_path='./chromedriver.exe',options=opts)
        elif browser == 'FirefoxUrl':
            opts = webdriver.firefox.options.Options()
            opts = __addoptions__(opts,headless)
            driver = webdriver.Firefox(executable_path='./geckodriver.exe',options=opts)
        elif browser == 'IE.HTTP':
            opts = webdriver.ie.options.Options()
            opts = __addoptions__(opts,headless)
            driver = webdriver.Ie(executable_path='./IEDriverServer.exe',options=opts)
        elif browser == 'MSEdgeHTM':
            opts = webdriver.edge.options.Options()
            opts = __addoptions__(opts,headless)
            driver = webdriver.Edge(executable_path='./chromedriver.exe',options=opts)
        else:
            # try ie as probably old edge
            opts = webdriver.ie.options.Options()
            opts = __addoptions__(opts,headless)
            driver = webdriver.Ie(executable_path='./IEDriverServer.exe',options=opts)

    except WebDriverException as e:
        __logger__(e)
        return (0,e)
        
    try:
        # download confluence
        driver.get(url)
    except TimeoutException as e:
        __logger__(e)
        return (0,e)
    
    # wait for page load
    time.sleep(5)
    try:
        # check for confluence header
        driver.find_element_by_class_name('aui-header')
    except NoSuchElementException as e:
        # check if we need to sign in
        try:
            if email:
                __logger__(f'Signing in with {email:}...')
                input_field = driver.find_element_by_id('i0116')
                input_field.send_keys(email)
                btn = driver.find_element_by_id('idSIButton9')
                btn.click()
                time.sleep(5)
                driver.find_element_by_class_name('aui-header')
            else:
                msg = f"Confluence needs you to sign in, try running with 'headless=False' or provide an email and try again."
                __logger__(msg)
                return (0, msg)
        except NoSuchElementException as e:
            if headless:
                msg = f"Confluence hasn't loaded, try running with 'headless=False' to identify the issue."
            else:
                msg = f"Confluence hasn't loaded."
            __logger__(msg)
            return (0, msg)
        except Exception as e:
            __logger__(e)
            return(0, e)

    # parse html
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # quit driver as we're finished with it now
    __logger__('Closing browser...')
    driver.quit()

    try:
        header = soup.find('h1',{'id':'title-text'})
        file_name = './' + header.text.replace(': DTA Technical Analysis','').strip() + '.def'
    except Exception as e:
        __logger__(e)
        return (0,e)

    tables = soup.find_all(class_='table-wrap')
    config = []

    for table in tables:
        # find the table header and check for a column with correct column(s)
        thead = table.find('thead')
        column_mapping = None
        column_position = None
        description_position = None
        column_mapping_positions = {
            'Data Type': None,
            'Nullable': None,
            'Column': None
            }
        column_definition = None
        column_definition_positions = {
            'Description': None,
            'Data Element Type': None,
            'Column': None
            }
        if thead:
            # if we have a header, check the column names
            cols = thead.contents[0]
            # check name of each column
            for i,c in enumerate(cols):
                column_header = c.find('div',class_='tablesorter-header-inner').text
                if column_header in ['Source Column','Transformation','Data Type','Default Value','Nullable']:
                    # found column mapping
                    column_mapping = True
                    if column_header in column_mapping_positions.keys():
                        column_mapping_positions[column_header] = i
                elif column_header in ['Business Term','Data Element Type']:
                    # found column definition
                    column_definition = True
                    if column_header in column_definition_positions.keys():
                        column_definition_positions[column_header] = i
                elif column_header == 'Column':
                    # found column column
                    if column_mapping and not column_mapping_positions['Column']:
                        # column mapping table found but column column not yet found
                        column_mapping_positions['Column'] = i
                    elif column_definition and not column_definition_positions['Column']:
                        # column definition table found but column column not yet found
                        column_definition_positions['Column'] = i
                    else:
                        column_position = i
                elif column_header == 'Description':
                    if column_definition and not column_definition_positions['Description']:
                        column_definition_positions['Description'] = i
                    else:
                        description_position = i

        if column_mapping:
            if not column_mapping_positions['Column']:
                column_mapping_positions['Column'] = column_position
            tbody = table.find('tbody')
            for row in tbody:
                index = None
                for i, item in enumerate(config):
                    if item['name'] == row.contents[column_mapping_positions['Column']].text.lower():
                        index == i
                        break

                if index != None:
                    column = item
                else:
                    column = {}

                column["name"] = f"{row.contents[column_mapping_positions['Column']].text.lower()}"
                column["type"] = f"{row.contents[column_mapping_positions['Data Type']].text.upper()}"
                column["mode"] = f"{row.contents[column_mapping_positions['Nullable']].text.upper()}"

                if index == None:
                    config.append(column)
                    
        if column_definition:
            if not column_definition_positions['Column']:
                column_definition_positions['Column'] = column_position
            if not column_definition_positions['Description']:
                column_definition_positions['Description'] = description_position
            tbody = table.find('tbody')
            for row in tbody:
                index = None
                for i, item in enumerate(config):
                    try:
                        if item['name'] == row.contents[column_definition_positions['Column']].text:
                            index = i
                            break
                    except TypeError as e:
                        continue
                    except Exception as e:
                        __logger__(e)
                        

                if index != None:
                    column = item
                else:
                    column = {}

                column["name"] = f"{row.contents[column_definition_positions['Column']].text.lower()}"
                column["description"] = f"{row.contents[column_definition_positions['Description']].text}"
                column["poicyTags"] = {'names': [f"{row.contents[column_definition_positions['Data Element Type']].text}"]}

                if index == None:
                    config.append(column)
    
    try:
        def_file = open(file_name,'w')
        def_file.write('[\n')
        for i, item in enumerate(config):
            if i > 0:
                def_file.write(',\n')
            def_file.write(__prettifydict__(item))
        def_file.write('\n]')
        def_file.close()    
    except Exception as e:
        __logger__(e)
        return (0,e)

    msg = f'Config ({file_name}) generated.'
    __logger__(msg)
    return (1,msg)

if __name__=='__main__':
    uri = 'https://confluence.bskyb.com/display/BusInt/dim_subscription_status%3A+DTA+Technical+Analysis'
    email = 'sean.conkie@sky.uk'
    headless = True
    createdef(uri,email,headless)
    
    # uri = sys.argv[1] if len(sys.argv) > 1 else ''
    # email = None
    # headless = True
    # if len(sys.argv) > 2:
    #     next_arg = sys.argv[2].split('=')
    #     if next_arg[0] == 'email' and len(next_arg) > 1:
    #         email = next_arg[1]
    # if len(sys.argv) > 3:
    #     if next_arg[0] == 'headless' and len(next_arg) > 1:
    #         headless = next_arg[1]


    # if uri == '':
    #     msg = 'No url supplied.'
    #     __logger__(msg)
    # else:    
    #     createdef(uri,email,headless)