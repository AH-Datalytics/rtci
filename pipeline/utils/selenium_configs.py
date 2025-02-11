from selenium import webdriver
from selenium.webdriver.firefox.options import Options


# ignore: port configs for remote selenium testing
#
# options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # example
# driver = webdriver.Remote("http://localhost:4444/wd/hub", options=options)

# options = webdriver.FirefoxOptions()
# options.add_argument("--headless")  # example
# driver = webdriver.Remote("http://localhost:4445/wd/hub", options=options)
#
# until here


def firefox_driver(self):
    options = Options()
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
