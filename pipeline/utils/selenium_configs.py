from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.chrome import ChromeDriverManager


# ***** ignore: port configs for remote selenium testing
#
# options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # example
# driver = webdriver.Remote("http://localhost:4444/wd/hub", options=options)

# options = webdriver.FirefoxOptions()
# options.add_argument("--headless")  # example
# driver = webdriver.Remote("http://localhost:4445/wd/hub", options=options)
#
# until here *****


def chrome_driver(self):
    """
    sets up a chrome webdriver for selenium scraping
    """
    # preferences are used here to specify download location for files during scraping
    prefs = {
        "download.default_directory": self.download_dir,  # set `self.download_dir` based on scrape
        "download.prompt_for_download": False,  # disable download prompts
        "download.directory_upgrade": True,  # create `self.download_dir` directory if it doesn't exist
        # "safebrowsing.enabled": True,  # enable safe browsing (optional)
    }

    # instantiate the options for the chrome driver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")

    # memory-saving argument, tells the chrome driver to save
    # temporary files in `/tmp` instead of in `/dev/shm`, since the latter
    # may have too little storage in a docker container configuration
    chrome_options.add_argument("--disable-dev-shm-usage")

    # make the driver invisible (no screen) unless explicitly stated as an argument to the scrape
    # (`--visible` can be used for local testing but not in the docker/remote server
    # environment, because the server does not have access to a screen)
    if not self.args.visible:
        chrome_options.add_argument("--headless")

    # add the preferences as an experimental option
    chrome_options.add_experimental_option("prefs", prefs)

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )


def firefox_driver(self):
    """
    sets up a firefox webdriver for selenium scraping
    (note: this driver isn't being used anywhere at present)
    """
    options = Options()
    options.add_argument("-headless")
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.manager.focusWhenStarting", False)
    options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk",
        "text/csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/octet-stream,"
        "application/vnd.ms-excel",
    )
    options.set_preference("browser.helperApps.alwaysAsk.force", False)
    options.set_preference("browser.download.manager.alertOnEXEOpen", False)
    options.set_preference("browser.download.manager.closeWhenDone", True)
    options.set_preference("browser.download.manager.showAlertOnComplete", False)
    options.set_preference("browser.download.manager.useWindow", False)
    options.enable_downloads = True

    # specify download directory for files within cwd
    options.set_preference("browser.download.dir", self.download_dir)

    return webdriver.Firefox(options=options)
