from decimal import Decimal

import pytest
from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

MENU_URL = "https://coffee-cart.app/"
CART_URL = "https://coffee-cart.app/cart"


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


@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 5)


def go_to_cart_tab(driver: WebDriver):
    link: WebElement = driver.find_element(By.CSS_SELECTOR, "a[href='/cart']")
    link.click()


def test_empty_cart(driver: WebDriver):
    driver.get(CART_URL)

    paragraph: WebElement = driver.find_element(By.CSS_SELECTOR, "div.list p")

    assert paragraph.text == "No coffee, go add some."


def add_every_coffee_to_cart(driver: WebDriver, wait: WebDriverWait):
    driver.get(MENU_URL)
    entry_buttons: list[WebElement] = list(map(lambda element: element.find_element(By.CSS_SELECTOR, "div div.cup"), driver.find_elements(By.CSS_SELECTOR, "li[data-v-a9662a08]")))

    for coffee_button in entry_buttons:
        coffee_button.click()

    go_to_cart_tab(driver)
    wait.until(EC.visibility_of_element_located((By.TAG_NAME,"body")))


def test_list_header_in_cart(driver: WebDriver, wait:WebDriverWait):
    add_every_coffee_to_cart(driver, wait)

    header: WebElement = driver.find_element(By.CSS_SELECTOR, "li.list-header")
    columns: list[WebElement] = header.find_elements(By.TAG_NAME, "div")

    assert len(columns) >= 3
    assert columns[0].text == "Item"
    assert columns[1].text == "Unit"
    assert columns[2].text == "Total"


def get_ordered_items_entries(driver: WebDriver) -> list[WebElement]:
    return driver.find_elements(By.CSS_SELECTOR, "ul:not(.cart-preview) li.list-item")


def test_entries_number(driver: WebDriver, wait: WebDriverWait):
    add_every_coffee_to_cart(driver, wait)
    entry_rows: list[WebElement] = get_ordered_items_entries(driver)

    assert len(entry_rows) == 9


def get_entry_unit_price(entry: WebElement) -> Decimal:
    price_span: WebElement = entry.find_element(By.CSS_SELECTOR, "div span.unit-desc")
    price_with_amount: str = price_span.text

    price_text: str = price_with_amount.split("x")[0].strip()
    return Decimal(price_text[1:])


def get_entry_amount(entry: WebElement) -> int:
    amount_span: WebElement = entry.find_element(By.CSS_SELECTOR, "div span.unit-desc")
    price_with_amount: str = amount_span.text

    amount_text: str = price_with_amount.split("x")[1].strip()
    return int(amount_text)


def get_add_button(entry: WebElement) -> WebElement:
    return entry.find_element(By.CSS_SELECTOR, "div div.unit-controller button")


def get_remove_button(entry: WebElement) -> WebElement:
    return entry.find_elements(By.CSS_SELECTOR, "div div.unit-controller button")[1]


def get_entry_total_price(entry: WebElement) -> Decimal:
    total_price_div: WebElement = entry.find_elements(By.CSS_SELECTOR, ":scope > div")[2]
    total_price_text: str = total_price_div.text[1:]

    return Decimal(total_price_text)


def get_remove_entry_button(entry: WebElement) -> WebElement:
    return entry.find_element(By.CSS_SELECTOR, "div button[class='delete']")


def test_entry_names_are_displayed(driver: WebDriver, wait: WebDriverWait):
    add_every_coffee_to_cart(driver, wait)

    cart_entries: list[WebElement] = get_ordered_items_entries(driver)

    for entry in cart_entries:
        assert entry.is_displayed()


def test_unit_prices_are_non_negative(driver: WebDriver, wait: WebDriverWait):
    add_every_coffee_to_cart(driver, wait)

    cart_entries: list[WebElement] = get_ordered_items_entries(driver)

    for entry in cart_entries:
        unit_price: Decimal = get_entry_unit_price(entry)

        assert unit_price >= 0


def test_entry_amount_is_positive(driver: WebDriver, wait: WebDriverWait):
    add_every_coffee_to_cart(driver, wait)

    cart_entries: list[WebElement] = get_ordered_items_entries(driver)

    for entry in cart_entries:
        amount: int = get_entry_amount(entry)

        assert amount > 0


def test_add_buttons_are_displayed(driver: WebDriver, wait: WebDriverWait):
    add_every_coffee_to_cart(driver, wait)

    cart_entries: list[WebElement] = get_ordered_items_entries(driver)

    for entry in cart_entries:
        add_button: WebElement = get_add_button(entry)

        assert add_button.is_displayed()


def test_remove_buttons_are_displayed(driver: WebDriver, wait: WebDriverWait):
    add_every_coffee_to_cart(driver, wait)

    cart_entries: list[WebElement] = get_ordered_items_entries(driver)

    for entry in cart_entries:
        remove_button: WebElement = get_remove_button(entry)

        assert remove_button.is_displayed()


def test_total_entry_price_is_valid_initially(driver: WebDriver, wait: WebDriverWait):
    add_every_coffee_to_cart(driver, wait)

    cart_entries: list[WebElement] = get_ordered_items_entries(driver)

    for entry in cart_entries:
        unit_price: Decimal = get_entry_unit_price(entry)
        total_price: Decimal = get_entry_total_price(entry)

        assert unit_price == total_price


def test_adding_coffees_changes_amount_and_total_entry_price(driver: WebDriver, wait: WebDriverWait):
    repeats = 3

    add_every_coffee_to_cart(driver, wait)

    cart_entries: list[WebElement] = get_ordered_items_entries(driver)

    for entry in cart_entries:
        add_button: WebElement = get_add_button(entry)
        unit_price: Decimal = get_entry_unit_price(entry)

        for expected_amount in range(1, repeats+1):
            expected_price = unit_price * expected_amount
            total_price = get_entry_total_price(entry)
            amount = get_entry_amount(entry)

            assert amount == expected_amount
            assert total_price == expected_price

            add_button.click()


def test_removing_coffees_changes_amount_and_total_entry_price(driver: WebDriver, wait: WebDriverWait):
    repeats = 3

    add_every_coffee_to_cart(driver, wait)

    cart_entries: list[WebElement] = get_ordered_items_entries(driver)

    for entry in cart_entries:
        add_button: WebElement = get_add_button(entry)

        for _ in range(repeats - 1):
            add_button.click()

        remove_button: WebElement = get_remove_button(entry)
        unit_price: Decimal = get_entry_unit_price(entry)

        for expected_amount in range(repeats, 0, -1):
            expected_price = unit_price * expected_amount
            total_price = get_entry_total_price(entry)
            amount = get_entry_amount(entry)

            assert amount == expected_amount
            assert total_price == expected_price

            remove_button.click()


def test_remove_entry_button_deletes_entire_entry(driver: WebDriver, wait: WebDriverWait):
    repeats = 2

    add_every_coffee_to_cart(driver, wait)

    cart_entries: list[WebElement] = get_ordered_items_entries(driver)
    expected_size = len(cart_entries)

    while len(cart_entries) > 0:
        assert len(cart_entries) == expected_size

        entry: WebElement = cart_entries[0]

        add_button: WebElement = get_add_button(entry)
        remove_entry_button: WebElement = get_remove_entry_button(entry)

        for _ in range(repeats):
            add_button.click()

        remove_entry_button.click()
        expected_size -= 1
        cart_entries = get_ordered_items_entries(driver)


def test_removing_single_item_removes_entire_entry(driver: WebDriver, wait: WebDriverWait):
    add_every_coffee_to_cart(driver, wait)

    cart_entries: list[WebElement] = get_ordered_items_entries(driver)
    expected_size = len(cart_entries)

    while len(cart_entries) > 0:
        assert len(cart_entries) == expected_size

        entry: WebElement = cart_entries[0]

        remove_button: WebElement = get_remove_button(entry)

        remove_button.click()
        expected_size -= 1
        cart_entries = get_ordered_items_entries(driver)


def test_total_price_of_cart_is_valid(driver: WebDriver, wait: WebDriverWait):
    repeats = 3
    expected_total_cart_price = Decimal(0)

    add_every_coffee_to_cart(driver, wait)

    cart_entries: list[WebElement] = get_ordered_items_entries(driver)

    for entry in cart_entries:
        add_button: WebElement = get_add_button(entry)

        for _ in range(repeats):
            add_button.click()

        expected_total_cart_price += get_entry_total_price(entry)

    total_price_text: str = driver.find_element(By.CSS_SELECTOR, "div.pay-container button.pay").text
    total_price = Decimal(total_price_text[len("Total: $"):]) # Remove "Total: $" preceding text

    assert total_price == expected_total_cart_price