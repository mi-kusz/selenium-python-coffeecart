import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver import Firefox

MENU_URL = "https://coffee-cart.app/"
CART_URL = "https://coffee-cart.app/cart"
GITHUB_URL = "https://coffee-cart.app/github"

URLS = [MENU_URL, CART_URL, GITHUB_URL]


@pytest.fixture(scope="module")
def driver_service():
    driver_service = Service("/snap/bin/geckodriver")
    return driver_service


@pytest.fixture
def driver(driver_service):
    options = Options()
    options.add_argument("--headless")
    driver = Firefox(options=options, service=driver_service)

    yield driver

    driver.quit()


def get_navigation(driver: WebDriver) -> WebElement:
    return driver.find_element(By.CSS_SELECTOR, "#app ul[data-v-bb7b5941]")


def get_navigation_links(driver: WebDriver) -> list[WebElement]:
    navigation = get_navigation(driver)

    return navigation.find_elements(By.CSS_SELECTOR, "li[data-v-bb7b5941]")


@pytest.mark.parametrize("url", URLS)
def test_navigation_is_displayed(driver: WebDriver, url: str):
    driver.get(url)
    navigation = get_navigation(driver)
    assert navigation.is_displayed()


@pytest.mark.parametrize("url", URLS)
def test_navigation_links_number(driver: WebDriver, url: str):
    driver.get(url)
    navigation_links = get_navigation_links(driver)

    assert len(navigation_links) == 3


@pytest.mark.parametrize("url", URLS)
def test_navigation_links_are_displayed(driver: WebDriver, url: str):
    driver.get(url)
    navigation_links = get_navigation_links(driver)

    for link in navigation_links:
        assert link.is_displayed()


@pytest.mark.parametrize("url", URLS)
def test_navigation_links_contain_valid_text_initially(driver: WebDriver, url: str):
    driver.get(url)
    navigation_links = get_navigation_links(driver)

    menu_link = navigation_links[0]
    cart_link = navigation_links[1]
    github_link = navigation_links[2]

    assert "menu" == menu_link.text
    assert "cart (0)" == cart_link.text
    assert "github" == github_link.text


@pytest.mark.parametrize("url", URLS)
def test_navigation_links_are_valid(driver: WebDriver, url: str):
    for link_index in range(3):
        driver.get(url)

        navigation_links = get_navigation_links(driver)

        link = navigation_links[link_index]
        link.click()

        assert URLS[link_index] == driver.current_url


def get_link_color(link: WebElement) -> str:
    return link.find_element(By.TAG_NAME, "a").value_of_css_property("color")


@pytest.mark.parametrize("url", URLS)
def test_current_page_is_in_different_color(driver: WebDriver, url: str):
    driver.get(url)

    navigation_links = get_navigation_links(driver)

    for link in navigation_links:
        if link.find_element(By.TAG_NAME, "a").get_attribute("href") == url:
            assert "rgb(218, 165, 32)" == get_link_color(link)
        else:
            assert "rgb(0, 0, 0)" == get_link_color(link)