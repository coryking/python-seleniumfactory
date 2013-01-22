import os
import urllib2
import json
import base64
from selenium import webdriver
from selenium import selenium

class ParseSauceURL:
    def __init__(self, url):
        self.url = url

        self.fields = {}
        fields = self.url.split(':')[1][1:].split('&')
        for field in fields:
            [key, value] = field.split('=')
            self.fields[key] = value

    def getValue(self, key):
        if key in self.fields:
            return self.fields[key]
        else:
            return ""

    def getUserName(self):
        return self.getValue("username")

    def getAccessKey(self):
        return self.getValue("access-key")

    def getJobName(self):
        return self.getValue("job-name")

    def getOS(self):
        return self.getValue("os")

    def getBrowser(self):
        return self.getValue('browser')

    def getBrowserVersion(self):
        return self.getValue('browser-version')

    def getFirefoxProfileURL(self):
        return self.getValue('firefox-profile-url')

    def getMaxDuration(self):
        try:
            return int(self.getValue('max-duration'))
        except:
            return 0

    def getIdleTimeout(self):
        try:
            return int(self.getValue('idle-timeout'))
        except:
            return 0

    def getUserExtensionsURL(self):
        return self.getValue('user-extensions-url')

    def toJSON(self):
        return json.dumps(self.fields, sort_keys=False)


url = 'https://saucelabs.com/rest/%s/%s/%s'

"""
This class provides several helper methods to invoke the Sauce REST API.
"""
class SauceRest:
    def __init__(self, user, key):
        self.user = user
        self.key = key

    def buildUrl(self, version, suffix):
        return url %(version, self.user, suffix)

    """
    Updates a Sauce Job with the data contained in the attributes dict
    """
    def update(self, id, attributes):
        url = self.buildUrl("v1", "jobs/" + id)
        data = json.dumps(attributes)
        return self.invokePut(url, self.user, self.key, data)

    """
    Retrieves the details for a Sauce job in JSON format
    """
    def get(self, id):
        url = self.buildUrl("v1", "jobs/" + id)
        return self.invokeGet(url, self.user, self.key)

    def invokePut(self, theurl, username, password, data):
        request = urllib2.Request(theurl, data, {'content-type': 'application/json'})
        base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
        request.add_header("Authorization", "Basic %s" % base64string)
        request.get_method = lambda: 'PUT'
        htmlFile = urllib2.urlopen(request)
        return htmlFile.read()

    def invokeGet(self, theurl, username, password):
        request = urllib2.Request(theurl)
        base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
        request.add_header("Authorization", "Basic %s" % base64string)
        htmlFile = urllib2.urlopen(request)
        return htmlFile.read()

"""
This class wraps a webdriver/selenium instance.  It delegates most method calls to the underlying webdriver/selenium
instance, and provides some helper methods to set the build number and job status using the Sauce REST API.

It also outputs the Sauce Session ID, which will be parsed by the Jenkins/Bamboo plugins so as to associate the CI build with
the Sauce job.
"""
class Wrapper:
    def __init__(self, selenium, parse):
        self.__dict__['selenium'] = selenium
        self.username = parse.getUserName()
        self.accessKey = parse.getAccessKey()
        self.jobName = parse.getJobName()

    def id(self):
        if hasattr(self.selenium, 'session_id'):
            return self.selenium.session_id
        else:
            return self.selenium.sessionId

    def dump_session_id(self):
        print "\rSauceOnDemandSessionID=%s job-name=%s" % (self.id(), self.jobName)

    def set_build_number(self, buildNumber):
        sauceRest = SauceRest(self.username, self.accessKey)
        sauceRest.update(self.id(), {'build': buildNumber})

    def job_passed(self):
        sauceRest = SauceRest(self.username, self.accessKey)
        sauceRest.update(self.id(), {'passed': True})

    def job_failed(self):
        sauceRest = SauceRest(self.username, self.accessKey)
        sauceRest.update(self.id(), {'passed': False})

    # automatic delegation:
    def __getattr__(self, attr):
        return getattr(self.selenium, attr)

    def __setattr__(self, attr, value):
        return setattr(self.selenium, attr, value)

"""
  Simple interface factory to create Selenium objects, inspired by the SeleniumFactory interface
  from https://github.com/infradna/selenium-client-factory for Java.

  <p>
  Compared to directly initializing {@link com.thoughtworks.selenium.DefaultSelenium}, this additional indirection
  allows the build script or a CI server to control how you connect to the selenium.
  This makes it easier to run the same set of tests in different environments without
  modifying the test code.

  <p>
  This is analogous to how you connect to JDBC &mdash; you normally don't directly
  instantiate a specific driver, and instead you do {@link DriverManager#getConnection(String)}.
"""
class SeleniumFactory:
    def __init__(self):
        pass

    """
     Uses a driver specified by the 'SELENIUM_DRIVER' environment variable,
     and run the test against the domain specified in 'SELENIUM_URL' system property or the environment variable.
     If no variables exist, a local Selenium driver is created.
    """
    def create(self):
        if 'SELENIUM_STARTING_URL' not in os.environ:
            startingUrl = "http://saucelabs.com"
        else:
            startingUrl = os.environ['SELENIUM_STARTING_URL']

        if 'SELENIUM_DRIVER' in os.environ and  'SELENIUM_HOST' in os.environ and 'SELENIUM_PORT' in os.environ:
            parse = ParseSauceURL(os.environ["SELENIUM_DRIVER"])
            driver = selenium(os.environ['SELENIUM_HOST'], os.environ['SELENIUM_PORT'], parse.toJSON(), startingUrl)
            driver.start()

            if parse.getMaxDuration() != 0:
                driver.set_timeout(parse.getMaxDuration())

            wrapper = Wrapper(driver, parse)
            wrapper.dump_session_id()
            return wrapper
        else:
            driver = selenium("localhost", 4444, "*firefox", startingUrl)
            driver.start()
            return driver

    """
     Uses a driver specified by the 'SELENIUM_DRIVER' system property or the environment variable,
     and run the test against the domain specified in 'SELENIUM_STARTING_URL' system property or the environment variable.
     If no variables exist, a local Selenium web driver is created.
    """
    def createWebDriver(self):
        if 'SELENIUM_STARTING_URL' not in os.environ:
            startingUrl = "http://saucelabs.com"
        else:
            startingUrl = os.environ['SELENIUM_STARTING_URL']

        if 'SELENIUM_DRIVER' in os.environ and 'SELENIUM_HOST' in os.environ and 'SELENIUM_PORT' in os.environ:
            parse = ParseSauceURL(os.environ["SELENIUM_DRIVER"])

            desired_capabilities = {}
            if parse.getBrowser() == 'android':
                desired_capabilities = webdriver.DesiredCapabilities.ANDROID
            elif parse.getBrowser() == 'googlechrome':
                desired_capabilities = webdriver.DesiredCapabilities.CHROME
            elif parse.getBrowser() == 'firefox':
                desired_capabilities = webdriver.DesiredCapabilities.FIREFOX
            elif parse.getBrowser() == 'htmlunit':
                desired_capabilities = webdriver.DesiredCapabilities.HTMLUNIT
            elif parse.getBrowser() == 'iexplore':
                desired_capabilities = webdriver.DesiredCapabilities.INTERNETEXPLORER
            elif parse.getBrowser() == 'iphone':
                desired_capabilities = webdriver.DesiredCapabilities.IPHONE
            else:
                desired_capabilities = webdriver.DesiredCapabilities.FIREFOX

            desired_capabilities['version'] = parse.getBrowserVersion()

            if 'SELENIUM_PLATFORM' in os.environ:
                desired_capabilities['platform'] = os.environ['SELENIUM_PLATFORM']
            else:
            #work around for name issues in Selenium 2
                if 'Windows 2003' in parse.getOS():
                    desired_capabilities['platform'] = 'XP'
                elif 'Windows 2008' in parse.getOS():
                    desired_capabilities['platform'] = 'VISTA'
                elif 'Linux' in parse.getOS():
                    desired_capabilities['platform'] = 'LINUX'
                else:
                    desired_capabilities['platform'] = parse.getOS()

            desired_capabilities['name'] = parse.getJobName()

            command_executor="http://%s:%s@%s:%s/wd/hub"%(parse.getUserName(), parse.getAccessKey(
            ), os.environ['SELENIUM_HOST'], os.environ['SELENIUM_PORT'])

            #make sure the test doesn't run forever if if the test crashes
            if parse.getMaxDuration() != 0:
                desired_capabilities['max-duration'] = parse.getMaxDuration()
                desired_capabilities['command-timeout'] = parse.getMaxDuration()

            if parse.getIdleTimeout() != 0:
                desired_capabilities['idle-timeout'] = parse.getIdleTimeout()

            driver=webdriver.Remote(desired_capabilities=desired_capabilities, command_executor=command_executor)
            driver.get(startingUrl)
            wrapper = Wrapper(driver, parse)
            wrapper.dump_session_id()
            return wrapper

        else:
            driver = webdriver.Firefox()
            driver.get(startingUrl)
            return driver
