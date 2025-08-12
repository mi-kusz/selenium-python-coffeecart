import re

import pytest
from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver import Firefox, ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from decimal import Decimal
from selenium.webdriver.support import expected_conditions as EC


URL = "https://coffee-cart.app/"

VALID_ENGLISH_NAMES = [
    "Espresso",
    "Espresso Macchiato",
    "Cappuccino",
    "Mocha",
    "Flat White",
    "Americano",
    "Cafe Latte",
    "Espresso Con Panna",
    "Cafe Breve"
]

VALID_CHINESE_NAMES = [
    "特浓咖啡",
    "浓缩玛奇朵",
    "卡布奇诺",
    "摩卡",
    "平白咖啡",
    "美式咖啡",
    "拿铁",
    "浓缩康宝蓝",
    "半拿铁"
]

ITEMS_TO_PROMO = 3


@pytest.fixture(scope="module")
def driver_service():
    driver_service = Service("/snap/bin/geckodriver")
    return driver_service


@pytest.fixture
def driver(driver_service):
    options = Options()
    #options.add_argument("--headless")
    driver = Firefox(options=options, service=driver_service)
    driver.get(URL)

    yield driver

    driver.quit()


@pytest.fixture
def wait(driver):
    return WebDriverWait(driver, 5)


def double_click(driver: WebDriver, element: WebElement):
    scroll_script = "arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});"
    driver.execute_script(scroll_script, element)

    ActionChains(driver).double_click(element).perform()


def move_cursor_away(driver: WebDriver):
    body: WebElement = driver.find_element(By.TAG_NAME, "body")

    width = body.size["width"]
    height = body.size["height"]

    ActionChains(driver).move_to_element_with_offset(body, -width / 2, -height / 2).perform()


def get_menu_entries(driver: WebDriver) -> list[WebElement]:
    return driver.find_elements(By.CSS_SELECTOR, "li[data-v-a9662a08]")


def get_entry_header(element: WebElement) -> WebElement:
    return element.find_element(By.TAG_NAME, "h4")


def get_entry_cup(element: WebElement) -> WebElement:
    return element.find_element(By.CSS_SELECTOR, "div div.cup")


def get_entry_price_text(element: WebElement) -> str:
    header: WebElement = get_entry_header(element)

    return header.find_element(By.TAG_NAME, "small").text


def get_entry_price(entry_element: WebElement) -> Decimal:
    price_text: str = get_entry_price_text(entry_element)
    number: str = price_text[1:] # Delete $ sign

    return Decimal(number)


def get_entry_name(element: WebElement) -> str:
    header: WebElement = get_entry_header(element)
    name_with_price: str = header.text

    price_text: str = get_entry_price_text(element)
    length_without_price: int = len(name_with_price) - len(price_text)

    return name_with_price[:length_without_price].strip()


def get_menu_entries_names(menu_entries: list[WebElement]) -> list[str]:
    return list(map(get_entry_name, menu_entries))


def get_pay_button(driver: WebDriver) -> WebElement:
    return driver.find_element(By.CSS_SELECTOR, "button.pay")


def assert_price_on_button_is_equal(driver: WebDriver, expected_price: Decimal):
    pay_button: WebElement = get_pay_button(driver)
    static_text = "Total: $"

    button_value = Decimal(pay_button.text[len(static_text):])

    assert button_value == expected_price


def get_cart_preview(driver: WebDriver) -> WebElement:
    return driver.find_element(By.CSS_SELECTOR, "ul.cart-preview")


def get_cart_preview_entries(driver: WebDriver) -> list[WebElement]:
    cart_preview: WebElement = get_cart_preview(driver)

    return cart_preview.find_elements(By.TAG_NAME, "li")


def get_cart_preview_entry_name(wait: WebDriverWait, cart_preview_entry: WebElement) -> str:
    span: WebElement = cart_preview_entry.find_element(By.TAG_NAME, "span")

    wait.until(lambda driver: span.text != "")

    return span.text


def get_cart_preview_entry_count(cart_preview_entry: WebElement) -> int:
    entry_count: WebElement = cart_preview_entry.find_element(By.CSS_SELECTOR, "span.unit-desc")

    # Omit "x" character
    return int(entry_count.text[1:].strip())


def get_add_button(cart_preview_entry: WebElement) -> WebElement:
    return cart_preview_entry.find_element(By.CSS_SELECTOR, "div.unit-controller button")


def get_remove_button(cart_preview_entry: WebElement) -> WebElement:
    return cart_preview_entry.find_elements(By.CSS_SELECTOR, "div.unit-controller button")[1]


def get_promo_element(driver: WebDriver) -> WebElement:
    return driver.find_element(By.CLASS_NAME, "promo")


def get_accept_promo_button(driver: WebDriver) -> WebElement:
    promo: WebElement = get_promo_element(driver)

    return promo.find_element(By.CSS_SELECTOR, "div.buttons button.yes")


def get_discard_promo_button(driver: WebDriver) -> WebElement:
    promo: WebElement = get_promo_element(driver)

    return promo.find_elements(By.CSS_SELECTOR, "div.buttons button")[1]


def hover_over_pay_button(driver: WebDriver):
    pay_button: WebElement = get_pay_button(driver)

    ActionChains(driver).move_to_element(pay_button).perform()


@pytest.mark.new
def test_menu_entries_number(driver: WebDriver):
    menu_entries: list[WebElement] = get_menu_entries(driver)

    assert len(menu_entries) == 9


def test_menu_entries_are_displayed(driver: WebDriver):
    menu_entries: list[WebElement] = get_menu_entries(driver)

    for menu_entry in menu_entries:
        assert menu_entry.is_displayed()


def test_menu_headers_english_names_are_valid(driver: WebDriver):
    menu_entries: list[WebElement] = get_menu_entries(driver)
    names: list[str] = get_menu_entries_names(menu_entries)

    assert names == VALID_ENGLISH_NAMES


def test_menu_headers_change_to_chinese_on_double_click(driver: WebDriver):
    menu_entries: list[WebElement] = get_menu_entries(driver)
    menu_headers: list[WebElement] = list(map(get_entry_header, menu_entries))

    for menu_header in menu_headers:
        double_click(driver, menu_header)

    names: list[str] = get_menu_entries_names(menu_entries)

    assert names == VALID_CHINESE_NAMES


def test_menu_headers_come_back_to_english_on_double_click(driver: WebDriver):
    menu_entries: list[WebElement] = get_menu_entries(driver)
    menu_headers: list[WebElement] = list(map(get_entry_header, menu_entries))

    for menu_header in menu_headers:
        double_click(driver, menu_header)
        double_click(driver, menu_header)

    names: list[str] = get_menu_entries_names(menu_entries)

    assert names == VALID_ENGLISH_NAMES


def test_menu_headers_change_color_on_hover(driver: WebDriver):
    menu_headers: list[WebElement] = list(map(get_entry_header, get_menu_entries(driver)))

    for menu_header in menu_headers:
        color_before: str = menu_header.value_of_css_property("color")

        ActionChains(driver).move_to_element(menu_header).perform()
        color_on_hover: str = menu_header.value_of_css_property("color")

        move_cursor_away(driver)
        color_on_mouse_off: str = menu_header.value_of_css_property("color")

        assert color_before == "rgb(0, 0, 0)"
        assert color_on_hover == "rgb(218, 165, 32)"
        assert color_on_mouse_off == "rgb(0, 0, 0)"


def test_prices_are_valid(driver: WebDriver):
    prices: list[str] = list(map(get_entry_price_text, get_menu_entries(driver)))
    regex = r"^\$[0-9]+\.[0-9]{2}$"

    for price in prices:
        assert re.fullmatch(regex, price)


# Works only in headful mode
def test_cups_rotate_on_hover(driver: WebDriver):
    cups = list(map(get_entry_cup, get_menu_entries(driver)))

    for cup in cups:
        transform_before: str = cup.value_of_css_property("transform")

        ActionChains(driver).move_to_element(cup).perform()
        transform_on_hover: str = cup.value_of_css_property("transform")

        move_cursor_away(driver)
        transform_on_mouse_off: str = cup.value_of_css_property("transform")

        assert transform_before == "none"
        assert "matrix" in transform_on_hover
        assert transform_on_mouse_off == "none"


def test_pay_button_is_displayed(driver: WebDriver):
    pay_button: WebElement = get_pay_button(driver)

    assert pay_button.is_displayed()


def test_price_is_zero_initially(driver: WebDriver):
    assert_price_on_button_is_equal(driver, Decimal(0))


def test_adding_coffees_increase_price(driver: WebDriver):
    menu_entries: list[WebElement] = get_menu_entries(driver)
    expected_price = Decimal(0)

    for menu_entry in menu_entries:
        cup_element: WebElement = get_entry_cup(menu_entry)
        coffee_price: Decimal = get_entry_price(menu_entry)

        cup_element.click()
        expected_price += coffee_price

        assert_price_on_button_is_equal(driver, expected_price)


def test_adding_the_same_coffee_to_cart_gives_valid_price(driver: WebDriver, wait: WebDriverWait):
    repeats = 10
    cups_number = 9

    for cup_index in range(cups_number):
        driver.refresh()

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-v-a9662a08]")))

        menu_entry: WebElement = get_menu_entries(driver)[cup_index]
        expected_price = Decimal(0)

        cup_element: WebElement = get_entry_cup(menu_entry)
        coffee_price: Decimal = get_entry_price(menu_entry)

        for _ in range(repeats):
            cup_element.click()
            expected_price += coffee_price

            assert_price_on_button_is_equal(driver, expected_price)


def test_cart_preview_does_not_show_up_without_hover(driver: WebDriver):
    with pytest.raises(NoSuchElementException):
        get_cart_preview(driver)

    menu_entry: WebElement = get_menu_entries(driver)[0]
    cup_element: WebElement = get_entry_cup(menu_entry)

    cup_element.click()

    cart_preview: WebElement = get_cart_preview(driver)

    assert not cart_preview.is_displayed()


def test_cart_preview_does_not_show_up_when_cart_is_empty(driver: WebDriver):
    hover_over_pay_button(driver)

    with pytest.raises(NoSuchElementException):
        get_cart_preview(driver)


def test_ordered_elements_show_up_in_cart_preview(driver: WebDriver, wait: WebDriverWait):
    cup_elements: list[WebElement] = list(map(get_entry_cup, get_menu_entries(driver)))

    for cup in cup_elements:
        cup.click()

    hover_over_pay_button(driver)

    cart_preview_entries: list[WebElement] = get_cart_preview_entries(driver)

    assert len(cart_preview_entries) == 9

    for preview_entry in cart_preview_entries:
        name: str = get_cart_preview_entry_name(wait, preview_entry)
        count: int = get_cart_preview_entry_count(preview_entry)

        assert name in VALID_ENGLISH_NAMES
        assert count == 1


def test_plus_and_minus_buttons_are_displayed_in_cart_preview(driver: WebDriver):
    cup_elements: list[WebElement] = list(map(get_entry_cup, get_menu_entries(driver)))

    for cup in cup_elements:
        cup.click()

    hover_over_pay_button(driver)

    cart_preview_entries: list[WebElement] = get_cart_preview_entries(driver)

    for cart_preview_entry in cart_preview_entries:
        plus_button: WebElement = get_add_button(cart_preview_entry)
        minus_button: WebElement = get_remove_button(cart_preview_entry)

        assert plus_button.is_displayed()
        assert minus_button.is_displayed()


def test_plus_and_minus_buttons_add_and_remove_elements_from_cart(driver: WebDriver):
    cup_elements: list[WebElement] = list(map(get_entry_cup, get_menu_entries(driver)))

    for cup in cup_elements:
        cup.click()

    hover_over_pay_button(driver)

    cart_preview_entries: list[WebElement] = get_cart_preview_entries(driver)

    for cart_preview_entry in cart_preview_entries:
        plus_button: WebElement = get_add_button(cart_preview_entry)
        minus_button: WebElement = get_remove_button(cart_preview_entry)

        plus_button.click()

        count: int = get_cart_preview_entry_count(cart_preview_entry)
        assert count == 2

        minus_button.click()

        count = get_cart_preview_entry_count(cart_preview_entry)
        assert count == 1


def test_removing_single_element_from_preview_delete_entry(driver: WebDriver):
    cup_elements: list[WebElement] = list(map(get_entry_cup, get_menu_entries(driver)))

    for cup in cup_elements:
        cup.click()

    hover_over_pay_button(driver)

    cart_preview_entries: list[WebElement] = get_cart_preview_entries(driver)
    expected_entries = len(cart_preview_entries)

    while True:
        assert expected_entries == len(cart_preview_entries)

        first_entry: WebElement = cart_preview_entries[0]
        delete_button: WebElement = get_remove_button(first_entry)

        delete_button.click()
        expected_entries -= 1

        if expected_entries == 0:
            with pytest.raises(NoSuchElementException):
                get_cart_preview(driver)
            break
        else:
            cart_preview_entries = get_cart_preview_entries(driver)


def test_promo_is_not_displayed_initially(driver: WebDriver):
    with pytest.raises(NoSuchElementException):
        get_promo_element(driver)


def test_ordering_three_coffees_shows_promo(driver: WebDriver):
    menu_entries: list[WebElement] = get_menu_entries(driver)
    counter = 0

    for menu_entry in menu_entries:
        if counter != 0 and counter % ITEMS_TO_PROMO == 0:
            # assert does not throw
            get_promo_element(driver)
        else:
            with pytest.raises(NoSuchElementException):
                get_promo_element(driver)

        cup_element: WebElement = get_entry_cup(menu_entry)
        cup_element.click()

        counter += 1


def add_items_to_cart_to_show_promo(driver: WebDriver) -> Decimal:
    menu_entry: WebElement = get_menu_entries(driver)[0]
    cup_element: WebElement = get_entry_cup(menu_entry)
    entry_price: Decimal = get_entry_price(menu_entry)

    expected_price = Decimal(0)

    for _ in range(ITEMS_TO_PROMO):
        expected_price += entry_price
        cup_element.click()

    return expected_price


def test_accept_and_discard_promo_buttons_are_displayed(driver: WebDriver):
    add_items_to_cart_to_show_promo(driver)

    accept_button: WebElement = get_accept_promo_button(driver)
    discard_button: WebElement = get_discard_promo_button(driver)

    assert accept_button.is_displayed()
    assert discard_button.is_displayed()


def test_discard_promo_button_does_not_change_anything(driver: WebDriver):
    expected_price: Decimal = add_items_to_cart_to_show_promo(driver)

    discard_button: WebElement = get_discard_promo_button(driver)
    discard_button.click()

    with pytest.raises(NoSuchElementException):
        get_promo_element(driver)

    assert_price_on_button_is_equal(driver, expected_price)


def test_accept_promo_button_adds_price(driver: WebDriver):
    discounted_price = Decimal(4)
    expected_price: Decimal = add_items_to_cart_to_show_promo(driver)

    accept_button: WebElement = get_accept_promo_button(driver)
    accept_button.click()

    expected_price += discounted_price

    assert_price_on_button_is_equal(driver, expected_price)


def test_accept_promo_adds_discounted_mocha_to_preview_on_the_first_place(driver: WebDriver, wait: WebDriverWait):
    add_items_to_cart_to_show_promo(driver)

    accept_button: WebElement = get_accept_promo_button(driver)
    accept_button.click()

    hover_over_pay_button(driver)

    cart_preview_first_entry: WebElement = get_cart_preview_entries(driver)[0]
    entry_name: str = get_cart_preview_entry_name(wait, cart_preview_first_entry)

    assert entry_name == "(Discounted) Mocha"


def is_sorted(strings: list[str]) -> bool:
    for i in range(1, len(strings)):
        if strings[i - 1] > strings[i]:
            return False

    return True


def test_items_in_cart_are_sorted_alphabetically(driver: WebDriver, wait: WebDriverWait):
    cup_elements: list[WebElement] = list(map(get_entry_cup, get_menu_entries(driver)))

    for cup in cup_elements:
        cup.click()

    hover_over_pay_button(driver)

    cart_preview_entry_names: list[str] = list(map(lambda entry: get_cart_preview_entry_name(wait, entry), get_cart_preview_entries(driver)))

    assert is_sorted(cart_preview_entry_names)


@pytest.mark.skip(reason="I think if a user gets a discounted item for ordering 3 items, the user should not be allowed to increase the number of discounted items without limit.")
def test_discounted_items_cannot_be_added_in_cart_preview(driver: WebDriver):
    add_items_to_cart_to_show_promo(driver)

    accept_promo_button: WebElement = get_accept_promo_button(driver)
    accept_promo_button.click()

    hover_over_pay_button(driver)

    discounted_entry: WebElement = get_cart_preview_entries(driver)[0]

    with pytest.raises(NoSuchElementException):
        get_add_button(discounted_entry)


def test_discounted_items_can_be_removed_in_cart_preview(driver: WebDriver):
    add_items_to_cart_to_show_promo(driver)

    accept_promo_button: WebElement = get_accept_promo_button(driver)
    accept_promo_button.click()

    hover_over_pay_button(driver)

    cart_preview_entries: list[WebElement] = get_cart_preview_entries(driver)
    initial_cart_preview_size = len(cart_preview_entries)

    discounted_entry: WebElement = cart_preview_entries[0]
    remove_button: WebElement = get_remove_button(discounted_entry)
    remove_button.click()

    cart_preview_entries = get_cart_preview_entries(driver)

    assert len(cart_preview_entries) == initial_cart_preview_size - 1


def test_promo_shows_up_every_three_basic_items_ordered_without_promo_items(driver: WebDriver):
    for _ in range(ITEMS_TO_PROMO):
        add_items_to_cart_to_show_promo(driver)

        assert get_promo_element(driver).is_displayed()


@pytest.mark.skip(reason="Discounted items counts to the promo counter. Example: 3 basic items -> Get promo item -> Need to order 2 (instead of 3) another items to get another promo.")
def test_promo_shows_up_every_three_basic_items_ordered_with_promo_items(driver: WebDriver):
    for _ in range(ITEMS_TO_PROMO):
        add_items_to_cart_to_show_promo(driver)

        assert get_promo_element(driver).is_displayed()

        get_accept_promo_button(driver).click()

@pytest.mark.skip(reason="There is no upper limit for discounted items")
def test_number_of_discounted_items_is_limited_by_number_of_basic_items(driver: WebDriver):
    for _ in range(3):
        add_items_to_cart_to_show_promo(driver)
        get_accept_promo_button(driver).click()

    # Currently in cart: 9 basic items and 3 discounted

    hover_over_pay_button(driver)

    cart_preview_entries: list[WebElement] = get_cart_preview_entries(driver)
    discounted_item_entry: WebElement = cart_preview_entries[0]
    basic_item_entry: WebElement = cart_preview_entries[1]

    remove_button: WebElement = get_remove_button(basic_item_entry)

    basic_item_count: int = get_cart_preview_entry_count(basic_item_entry)

    while basic_item_count > 0:
        maximum_of_discounted_items = basic_item_count // ITEMS_TO_PROMO

        if maximum_of_discounted_items == 0:
            with pytest.raises(StaleElementReferenceException):
                get_cart_preview_entry_count(discounted_item_entry)
            break
        else:
            discounted_item_count = get_cart_preview_entry_count(discounted_item_entry)

        assert discounted_item_count <= maximum_of_discounted_items

        remove_button.click()
        basic_item_count -= 1


def get_modal_element(driver: WebDriver) -> WebElement:
    return driver.find_element(By.CSS_SELECTOR, "div.modal-content")


def get_modal_name_input(driver: WebDriver) -> WebElement:
    modal: WebElement = get_modal_element(driver)

    return modal.find_element(By.CSS_SELECTOR, "input#name")


def get_modal_email_input(driver: WebDriver) -> WebElement:
    modal: WebElement = get_modal_element(driver)

    return modal.find_element(By.CSS_SELECTOR, "input#email")


def get_modal_promotion_checkbox(driver: WebDriver) -> WebElement:
    modal: WebElement = get_modal_element(driver)

    return modal.find_element(By.CSS_SELECTOR, "input#promotion")


def get_submit_payment_button(driver: WebDriver) -> WebElement:
    modal: WebElement = get_modal_element(driver)

    return modal.find_element(By.CSS_SELECTOR, "button#submit-payment")


def test_modal_is_not_displayed_initially(driver: WebDriver):
    modal: WebElement = get_modal_element(driver)

    assert not modal.is_displayed()


def test_modal_shows_up_after_pay_button_click(driver: WebDriver):
    pay_button: WebElement = get_pay_button(driver)
    modal: WebElement = get_modal_element(driver)

    pay_button.click()

    assert modal.is_displayed()


def test_modal_name_input_is_displayed(driver: WebDriver):
    pay_button: WebElement = get_pay_button(driver)
    pay_button.click()

    name_input: WebElement = get_modal_name_input(driver)

    assert name_input.is_displayed()


def test_modal_email_input_is_displayed(driver: WebDriver):
    pay_button: WebElement = get_pay_button(driver)
    pay_button.click()

    email_input: WebElement = get_modal_email_input(driver)

    assert email_input.is_displayed()


def test_modal_promo_input_is_displayed(driver: WebDriver):
    pay_button: WebElement = get_pay_button(driver)
    pay_button.click()

    promo_checkbox: WebElement = get_modal_promotion_checkbox(driver)

    assert promo_checkbox.is_displayed()


def test_modal_submit_input_is_displayed(driver: WebDriver):
    pay_button: WebElement = get_pay_button(driver)
    pay_button.click()

    submit_button: WebElement = get_submit_payment_button(driver)

    assert submit_button.is_displayed()


def test_modal_name_and_email_cannot_be_empty(driver: WebDriver):
    pay_button: WebElement = get_pay_button(driver)
    pay_button.click()

    submit_button: WebElement = get_submit_payment_button(driver)
    submit_button.click()

    # Modal does not disappear
    assert get_modal_element(driver).is_displayed()


def test_modal_email_cannot_be_empty(driver: WebDriver):
    pay_button: WebElement = get_pay_button(driver)
    pay_button.click()

    name_input: WebElement = get_modal_name_input(driver)
    name_input.send_keys("Test name")

    submit_button: WebElement = get_submit_payment_button(driver)
    submit_button.click()

    # Modal does not disappear
    assert get_modal_element(driver).is_displayed()


def test_modal_name_cannot_be_empty(driver: WebDriver):
    pay_button: WebElement = get_pay_button(driver)
    pay_button.click()

    email_input: WebElement = get_modal_email_input(driver)
    email_input.send_keys("test@test.com")

    submit_button: WebElement = get_submit_payment_button(driver)
    submit_button.click()

    # Modal does not disappear
    assert get_modal_element(driver).is_displayed()


def test_modal_email_must_be_valid(driver: WebDriver):
    pay_button: WebElement = get_pay_button(driver)
    pay_button.click()

    name_input: WebElement = get_modal_name_input(driver)
    name_input.send_keys("Test name")

    email_input: WebElement = get_modal_email_input(driver)
    email_input.send_keys("test")

    submit_button: WebElement = get_submit_payment_button(driver)
    submit_button.click()

    # Modal does not disappear
    assert get_modal_element(driver).is_displayed()


def test_modal_disappears_with_valid_data(driver: WebDriver):
    pay_button: WebElement = get_pay_button(driver)
    pay_button.click()

    name_input: WebElement = get_modal_name_input(driver)
    name_input.send_keys("Test name")

    email_input: WebElement = get_modal_email_input(driver)
    email_input.send_keys("test@test.com")

    submit_button: WebElement = get_submit_payment_button(driver)
    submit_button.click()

    assert not get_modal_element(driver).is_displayed()


def test_modal_checkbox_can_be_selected_and_unselected(driver: WebDriver):
    pay_button: WebElement = get_pay_button(driver)
    pay_button.click()

    checkbox_input: WebElement = get_modal_promotion_checkbox(driver)

    assert not checkbox_input.is_selected()

    checkbox_input.click()
    assert checkbox_input.is_selected()

    checkbox_input.click()
    assert not checkbox_input.is_selected()


def get_snackbar_element(driver: WebDriver) -> WebElement:
    return driver.find_element(By.CSS_SELECTOR, "div.snackbar.success")


def test_snackbar_is_not_displayed_initially(driver: WebDriver):
    with pytest.raises(NoSuchElementException):
        get_snackbar_element(driver)


def test_snackbar_shows_up_after_purchase(driver: WebDriver, wait: WebDriverWait):
    get_pay_button(driver).click()

    get_modal_name_input(driver).send_keys("Test name")
    get_modal_email_input(driver).send_keys("test@test.com")
    get_submit_payment_button(driver).click()

    snackbar: WebElement = get_snackbar_element(driver)

    wait.until(EC.visibility_of(snackbar))

    assert snackbar.is_displayed()


def test_snackbar_disappears_after_time(driver: WebDriver, wait: WebDriverWait):
    get_pay_button(driver).click()

    get_modal_name_input(driver).send_keys("Test name")
    get_modal_email_input(driver).send_keys("test@test.com")
    get_submit_payment_button(driver).click()

    snackbar: WebElement = get_snackbar_element(driver)

    wait.until(EC.invisibility_of_element(snackbar))

    assert not snackbar.is_displayed()