"""Functional tests for target.py.

Each function gets four groups of cases:
  * valid inputs          - normal, typical values
  * boundary values       - the exact edges where behaviour changes
  * invalid values        - right type, but a value the function must reject
  * wrong types           - inputs of the wrong data type

Exceptions are checked with the exact class and, where the message is
part of the contract, with ``match=``. ``pytest.approx`` is only used for
results that are genuinely inexact (floating point division / roots).
"""

import math
import re

import pytest

import target


# ---------------------------------------------------------------------------
# 1. is_adult  (Integer)
# ---------------------------------------------------------------------------
class TestIsAdult:
    @pytest.mark.parametrize(
        "age, expected",
        [
            (0, False),  # lower boundary of valid range
            (1, False),
            (17, False),  # just below the adult boundary
            (18, True),  # exact boundary
            (19, True),  # just above the boundary
            (65, True),
            (150, True),  # very large age
            (17.99, False),  # float just under boundary
            (18.0, True),  # float exactly on boundary
        ],
    )
    def test_valid_and_boundary(self, age, expected):
        result = target.is_adult(age)
        assert result is expected  # must be a real bool, not truthy/falsy

    @pytest.mark.parametrize("age", [-1, -0.5, -100])
    def test_negative_age_raises(self, age):
        with pytest.raises(ValueError, match="^age cannot be negative$"):
            target.is_adult(age)

    @pytest.mark.parametrize("age", ["18", None, [18], {"age": 18}])
    def test_wrong_type_raises(self, age):
        with pytest.raises(TypeError):
            target.is_adult(age)


# ---------------------------------------------------------------------------
# 2. celsius_to_fahrenheit  (Float)
# ---------------------------------------------------------------------------
class TestCelsiusToFahrenheit:
    @pytest.mark.parametrize(
        "celsius, expected",
        [
            (0, 32.0),  # freezing point
            (100, 212.0),  # boiling point
            (-40, -40.0),  # both scales meet
            (37, 98.6),  # body temperature (rounding needed)
            (-273.15, -459.67),  # absolute zero
            (36.6, 97.88),
            (1.234, 34.22),  # rounding to 2 decimals
            (0.005, 32.01),
        ],
    )
    def test_valid(self, celsius, expected):
        result = target.celsius_to_fahrenheit(celsius)
        assert result == expected  # rounded result must be exact
        assert isinstance(result, float)

    def test_result_has_at_most_two_decimals(self):
        result = target.celsius_to_fahrenheit(12.3456)
        assert result == round(result, 2)
        assert result == 54.22

    def test_large_value(self):
        assert target.celsius_to_fahrenheit(1_000_000) == 1_800_032.0

    @pytest.mark.parametrize("value", ["0", None, [0]])
    def test_wrong_type_raises(self, value):
        with pytest.raises(TypeError):
            target.celsius_to_fahrenheit(value)


# ---------------------------------------------------------------------------
# 3. count_vowels  (String)
# ---------------------------------------------------------------------------
class TestCountVowels:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("", 0),  # empty string boundary
            ("a", 1),  # single vowel
            ("b", 0),  # single consonant
            ("rhythm", 0),  # no vowels; 'y' is not a vowel
            ("aeiou", 5),
            ("AEIOU", 5),  # upper case counted
            ("AeIoU", 5),  # mixed case
            ("hello world", 3),
            ("Programming", 3),
            ("123 !?", 0),  # digits and punctuation
            ("   ", 0),  # whitespace only
            ("café", 1),  # accented e is not a plain vowel
            ("aaaa", 4),  # repeated vowels each counted
        ],
    )
    def test_valid(self, text, expected):
        result = target.count_vowels(text)
        assert result == expected
        assert type(result) is int

    @pytest.mark.parametrize("value", [None, 123, ["a", "e"], b"aeiou", True])
    def test_non_string_raises(self, value):
        with pytest.raises(TypeError, match="^text must be a string$"):
            target.count_vowels(value)


# ---------------------------------------------------------------------------
# 4. invert  (Boolean)
# ---------------------------------------------------------------------------
class TestInvert:
    @pytest.mark.parametrize("flag, expected", [(True, False), (False, True)])
    def test_valid(self, flag, expected):
        assert target.invert(flag) is expected

    def test_double_invert_returns_original(self):
        assert target.invert(target.invert(True)) is True

    # 0 and 1 behave like bools in Python but are NOT bools
    @pytest.mark.parametrize("value", [0, 1, None, "True", "", [], 0.0])
    def test_non_bool_raises(self, value):
        with pytest.raises(TypeError, match="^flag must be True or False$"):
            target.invert(value)


# ---------------------------------------------------------------------------
# 5. greet  (None)
# ---------------------------------------------------------------------------
class TestGreet:
    def test_default_argument_is_guest(self):
        assert target.greet() == "Hello, Guest!"

    @pytest.mark.parametrize("name", [None, "", " ", "    ", "\t", "\n", " \t\n "])
    def test_none_empty_or_blank_is_guest(self, name):
        assert target.greet(name) == "Hello, Guest!"

    @pytest.mark.parametrize(
        "name, expected",
        [
            ("Alice", "Hello, Alice!"),
            ("  Bob  ", "Hello, Bob!"),  # surrounding spaces stripped
            ("A", "Hello, A!"),  # single character
            ("Mary Jane", "Hello, Mary Jane!"),  # inner space kept
            ("guest", "Hello, guest!"),  # literal word is not special
            ("রহিম", "Hello, রহিম!"),  # unicode name
        ],
    )
    def test_valid_names(self, name, expected):
        result = target.greet(name)
        assert result == expected
        assert isinstance(result, str)

    @pytest.mark.parametrize("value", [123, ["Alice"], 1.5])
    def test_wrong_type_raises(self, value):
        # Non-strings have no .strip(), so Python raises AttributeError.
        with pytest.raises(AttributeError):
            target.greet(value)


# ---------------------------------------------------------------------------
# 6. find_max  (List)
# ---------------------------------------------------------------------------
class TestFindMax:
    @pytest.mark.parametrize(
        "numbers, expected",
        [
            ([5], 5),  # single element boundary
            ([1, 2, 3], 3),  # max at end
            ([3, 2, 1], 3),  # max at start
            ([1, 9, 2], 9),  # max in middle
            ([-5, -2, -9], -2),  # all negative
            ([0, 0, 0], 0),  # all equal
            ([2, 7, 7, 1], 7),  # duplicate maximum
            ([1.5, 2.5, 2.4], 2.5),  # floats
            ([1, 2.5, 2], 2.5),  # mixed int/float
            ([10**20, 1], 10**20),  # very large int
        ],
    )
    def test_valid(self, numbers, expected):
        result = target.find_max(numbers)
        assert result == expected
        assert type(result) is type(expected)

    def test_does_not_modify_input(self):
        numbers = [3, 1, 2]
        target.find_max(numbers)
        assert numbers == [3, 1, 2]

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="^list is empty$"):
            target.find_max([])

    @pytest.mark.parametrize("value", [None, 5])
    def test_wrong_type_raises(self, value):
        with pytest.raises(TypeError):
            target.find_max(value)

    def test_mixed_uncomparable_items_raise(self):
        with pytest.raises(TypeError):
            target.find_max([1, "a"])


# ---------------------------------------------------------------------------
# 7. get_price  (Dictionary)
# ---------------------------------------------------------------------------
PRICES = {"apple": 1.25, "bread": 3, "milk": 0, "": 9.99}


class TestGetPrice:
    @pytest.mark.parametrize(
        "item, expected",
        [
            ("apple", 1.25),
            ("bread", 3),
            ("milk", 0),  # falsy price must still be returned
            ("", 9.99),  # empty-string key is a valid key
        ],
    )
    def test_valid(self, item, expected):
        result = target.get_price(PRICES, item)
        assert result == expected
        assert type(result) is type(expected)

    def test_does_not_modify_dict(self):
        prices = {"tea": 2}
        target.get_price(prices, "tea")
        assert prices == {"tea": 2}

    @pytest.mark.parametrize("item", ["banana", "Apple", "apple ", None])
    def test_missing_item_raises(self, item):
        # KeyError's str() wraps the message in quotes, so match the core text.
        with pytest.raises(KeyError, match=re.escape(f"{item} not found")):
            target.get_price(PRICES, item)

    def test_empty_dict_raises(self):
        with pytest.raises(KeyError, match="apple not found"):
            target.get_price({}, "apple")

    def test_unhashable_item_raises(self):
        with pytest.raises(TypeError):
            target.get_price(PRICES, ["apple"])

    def test_non_dict_raises(self):
        with pytest.raises(TypeError):
            target.get_price(None, "apple")


# ---------------------------------------------------------------------------
# 8. swap  (Tuple)
# ---------------------------------------------------------------------------
class TestSwap:
    @pytest.mark.parametrize(
        "pair, expected",
        [
            ((1, 2), (2, 1)),
            (("a", "b"), ("b", "a")),
            ((1, "x"), ("x", 1)),  # mixed types
            ((None, 0), (0, None)),
            ((5, 5), (5, 5)),  # identical values
            (((1, 2), [3]), ([3], (1, 2))),  # nested values
        ],
    )
    def test_valid(self, pair, expected):
        result = target.swap(pair)
        assert result == expected
        assert type(result) is tuple

    def test_list_input_returns_tuple(self):
        result = target.swap([1, 2])
        assert result == (2, 1)
        assert type(result) is tuple

    @pytest.mark.parametrize("pair", [(), (1,), (1, 2, 3), (1, 2, 3, 4)])
    def test_wrong_length_raises(self, pair):
        with pytest.raises(ValueError, match="^pair must have exactly 2 values$"):
            target.swap(pair)

    @pytest.mark.parametrize("value", [None, 12])
    def test_wrong_type_raises(self, value):
        with pytest.raises(TypeError):
            target.swap(value)


# ---------------------------------------------------------------------------
# 9. common_items  (Set)
# ---------------------------------------------------------------------------
class TestCommonItems:
    @pytest.mark.parametrize(
        "set_a, set_b, expected",
        [
            ({1, 2, 3}, {2, 3, 4}, {2, 3}),
            ({1, 2}, {3, 4}, set()),  # disjoint
            ({1, 2}, {1, 2}, {1, 2}),  # identical
            ({1, 2, 3}, {2}, {2}),  # subset
            (set(), {1, 2}, set()),  # empty left
            ({1, 2}, set(), set()),  # empty right
            (set(), set(), set()),  # both empty
            ({"a", "B"}, {"A", "B"}, {"B"}),  # case sensitive
        ],
    )
    def test_valid(self, set_a, set_b, expected):
        result = target.common_items(set_a, set_b)
        assert result == expected
        assert isinstance(result, set)

    def test_is_symmetric(self):
        a, b = {1, 2, 3}, {3, 4}
        assert target.common_items(a, b) == target.common_items(b, a)

    def test_inputs_not_modified(self):
        a, b = {1, 2}, {2, 3}
        target.common_items(a, b)
        assert a == {1, 2} and b == {2, 3}

    def test_frozenset_input(self):
        assert target.common_items(frozenset({1, 2}), frozenset({2})) == {2}

    @pytest.mark.parametrize("set_a, set_b", [([1, 2], [2, 3]), ({1}, None), ("ab", {"a"})])
    def test_wrong_type_raises(self, set_a, set_b):
        with pytest.raises(TypeError):
            target.common_items(set_a, set_b)


# ---------------------------------------------------------------------------
# 10. is_leap_year  (Date)
# ---------------------------------------------------------------------------
class TestIsLeapYear:
    @pytest.mark.parametrize(
        "year, expected",
        [
            (2024, True),  # divisible by 4
            (2023, False),  # not divisible by 4
            (1900, False),  # divisible by 100 but not 400
            (2100, False),
            (1800, False),  # divisible by 200 but not 400
            (200, False),
            (2000, True),  # divisible by 400
            (1600, True),
            (4, True),  # first leap year
            (1, False),  # lowest valid year (boundary)
            (100, False),
            (400, True),
            (2, False),
            (9996, True),
        ],
    )
    def test_valid(self, year, expected):
        assert target.is_leap_year(year) is expected

    @pytest.mark.parametrize("year", [0, -1, -4, -400])
    def test_year_below_one_raises(self, year):
        with pytest.raises(ValueError, match="^year must be 1 or more$"):
            target.is_leap_year(year)

    @pytest.mark.parametrize("year", ["2024", None, [2024]])
    def test_wrong_type_raises(self, year):
        with pytest.raises(TypeError):
            target.is_leap_year(year)


# ---------------------------------------------------------------------------
# 11. to_int  (Type conversion)
# ---------------------------------------------------------------------------
class TestToInt:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (5, 5),
            (0, 0),
            (-7, -7),
            ("42", 42),
            ("-3", -3),
            ("  8 ", 8),  # surrounding whitespace allowed by int()
            ("007", 7),
            (3.9, 3),  # floats truncate toward zero
            (-3.9, -3),
            (0.0, 0),
            (10**30, 10**30),
        ],
    )
    def test_valid(self, value, expected):
        result = target.to_int(value)
        assert result == expected
        assert type(result) is int

    @pytest.mark.parametrize("value", [True, False])
    def test_bool_raises(self, value):
        with pytest.raises(TypeError, match="^bool is not allowed$"):
            target.to_int(value)

    @pytest.mark.parametrize("value", ["", "abc", "3.5", "1e3", "  "])
    def test_bad_string_raises(self, value):
        with pytest.raises(ValueError):
            target.to_int(value)

    @pytest.mark.parametrize("value", [None, [1], {"a": 1}])
    def test_wrong_type_raises(self, value):
        with pytest.raises(TypeError):
            target.to_int(value)

    @pytest.mark.parametrize(
        "value, exc", [(float("inf"), OverflowError), (float("nan"), ValueError)]
    )
    def test_special_floats_raise(self, value, exc):
        with pytest.raises(exc):
            target.to_int(value)


# ---------------------------------------------------------------------------
# 12. divide  (Math)
# ---------------------------------------------------------------------------
class TestDivide:
    @pytest.mark.parametrize(
        "a, b, expected",
        [
            (10, 2, 5.0),
            (7, 2, 3.5),
            (-9, 3, -3.0),
            (9, -3, -3.0),
            (-9, -3, 3.0),
            (0, 5, 0.0),  # zero numerator
            (5, 1, 5.0),
            (2.5, 0.5, 5.0),
        ],
    )
    def test_exact(self, a, b, expected):
        result = target.divide(a, b)
        assert result == expected
        assert isinstance(result, float)  # true division always gives float

    @pytest.mark.parametrize(
        "a, b, expected", [(1, 3, 0.3333333333), (2, 3, 0.6666666667), (0.1, 0.3, 0.3333333333)]
    )
    def test_inexact(self, a, b, expected):
        assert target.divide(a, b) == pytest.approx(expected)

    def test_very_small_divisor(self):
        assert target.divide(1, 1e-10) == pytest.approx(1e10)

    @pytest.mark.parametrize("b", [0, 0.0, -0.0])
    def test_divide_by_zero_raises(self, b):
        with pytest.raises(ZeroDivisionError, match="^cannot divide by zero$"):
            target.divide(5, b)

    def test_zero_by_zero_raises(self):
        with pytest.raises(ZeroDivisionError, match="^cannot divide by zero$"):
            target.divide(0, 0)

    @pytest.mark.parametrize("a, b", [("6", 2), (6, "2"), (None, 1)])
    def test_wrong_type_raises(self, a, b):
        with pytest.raises(TypeError):
            target.divide(a, b)


# ---------------------------------------------------------------------------
# 13. power  (Math)
# ---------------------------------------------------------------------------
class TestPower:
    @pytest.mark.parametrize(
        "base, exponent, expected",
        [
            (2, 3, 8),
            (5, 0, 1),  # anything to the 0 is 1
            (0, 0, 1),  # Python defines 0**0 == 1
            (0, 5, 0),
            (1, 1000, 1),
            (-2, 3, -8),  # odd exponent keeps sign
            (-2, 2, 4),  # even exponent removes sign
            (10, 1, 10),
            (2, 64, 18446744073709551616),
        ],
    )
    def test_integer_results(self, base, exponent, expected):
        result = target.power(base, exponent)
        assert result == expected
        assert type(result) is int

    @pytest.mark.parametrize(
        "base, exponent, expected",
        [(2, -1, 0.5), (2, -2, 0.25), (4, 0.5, 2.0), (2.5, 2, 6.25)],
    )
    def test_float_results(self, base, exponent, expected):
        result = target.power(base, exponent)
        assert result == expected
        assert isinstance(result, float)

    def test_inexact_result(self):
        assert target.power(2, 0.5) == pytest.approx(math.sqrt(2))

    def test_zero_to_negative_raises(self):
        with pytest.raises(ZeroDivisionError):
            target.power(0, -1)

    def test_negative_base_fractional_exponent_gives_complex(self):
        # Documents current behaviour (see "Suspected bugs" in README).
        result = target.power(-8, 1 / 3)
        assert isinstance(result, complex)

    def test_overflow_raises(self):
        with pytest.raises(OverflowError):
            target.power(10.0, 400)

    @pytest.mark.parametrize("base, exponent", [("2", 3), (2, "3"), (None, 2)])
    def test_wrong_type_raises(self, base, exponent):
        with pytest.raises(TypeError):
            target.power(base, exponent)


# ---------------------------------------------------------------------------
# 14. square_root  (Math)
# ---------------------------------------------------------------------------
class TestSquareRoot:
    @pytest.mark.parametrize(
        "x, expected",
        [(0, 0.0), (1, 1.0), (4, 2.0), (9, 3.0), (0.25, 0.5), (1e10, 1e5)],
    )
    def test_exact(self, x, expected):
        result = target.square_root(x)
        assert result == expected
        assert isinstance(result, float)

    @pytest.mark.parametrize("x", [2, 3, 0.5, 1e-10])
    def test_inexact(self, x):
        result = target.square_root(x)
        assert result == pytest.approx(x**0.5)
        assert result * result == pytest.approx(x)

    def test_negative_zero_is_allowed(self):
        assert target.square_root(-0.0) == 0.0

    @pytest.mark.parametrize("x", [-1, -0.0001, -100])
    def test_negative_raises(self, x):
        with pytest.raises(ValueError, match="^cannot take the square root of a negative number$"):
            target.square_root(x)

    @pytest.mark.parametrize("x", ["4", None, [4]])
    def test_wrong_type_raises(self, x):
        with pytest.raises(TypeError):
            target.square_root(x)


# ---------------------------------------------------------------------------
# 15. factorial  (Math)
# ---------------------------------------------------------------------------
class TestFactorial:
    @pytest.mark.parametrize(
        "n, expected",
        [
            (0, 1),  # boundary: 0! == 1
            (1, 1),
            (2, 2),
            (3, 6),
            (5, 120),
            (10, 3628800),
            (20, 2432902008176640000),
        ],
    )
    def test_valid(self, n, expected):
        result = target.factorial(n)
        assert result == expected
        assert type(result) is int

    def test_matches_math_factorial(self):
        assert target.factorial(50) == math.factorial(50)

    @pytest.mark.parametrize("n", [-1, -5, -100])
    def test_negative_raises(self, n):
        with pytest.raises(ValueError, match="^factorial is not defined for negative numbers$"):
            target.factorial(n)

    @pytest.mark.parametrize("n", [3.5, 2.0, "5", None])
    def test_wrong_type_raises(self, n):
        with pytest.raises(TypeError):
            target.factorial(n)


# ---------------------------------------------------------------------------
# 16. average  (Math)
# ---------------------------------------------------------------------------
class TestAverage:
    @pytest.mark.parametrize(
        "numbers, expected",
        [
            ([5], 5.0),  # single element boundary
            ([1, 2, 3], 2.0),
            ([1, 2], 1.5),
            ([-1, 1], 0.0),
            ([-2, -4], -3.0),
            ([0, 0, 0], 0.0),
            ([2.5, 3.5], 3.0),
        ],
    )
    def test_exact(self, numbers, expected):
        result = target.average(numbers)
        assert result == expected
        assert isinstance(result, float)

    @pytest.mark.parametrize("numbers, expected", [([1, 2, 2], 1.6666666667), ([0.1, 0.2], 0.15)])
    def test_inexact(self, numbers, expected):
        assert target.average(numbers) == pytest.approx(expected)

    def test_tuple_input(self):
        assert target.average((2, 4, 6)) == 4.0

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="^list is empty$"):
            target.average([])

    @pytest.mark.parametrize("value", [None, 5, ["1", "2"]])
    def test_wrong_type_raises(self, value):
        with pytest.raises(TypeError):
            target.average(value)
