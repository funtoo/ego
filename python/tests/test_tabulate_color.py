from unittest import TestCase
from python.third_party import tabulate_color


class Test(TestCase):

    def test__rst_escape_first_column(self):
        # GIVEN
        given_headers = ["A"]
        given_rows = ["a"]

        # WHEN
        new_rows, new_headers = tabulate_color._rst_escape_first_column(given_rows, given_headers)

        # THEN
        self.assertListEqual(['A'], new_headers)
        self.assertListEqual([['a']], new_rows)

    def test_escape_empty(self):
        # GIVEN
        given_headers = [""]
        given_rows = [""]

        # WHEN
        new_rows, new_headers = tabulate_color._rst_escape_first_column(given_rows, given_headers)

        # THEN
        self.assertListEqual(['..'], new_headers)
        self.assertListEqual([[]], new_rows)

    def test__rst_escape_first_column_multiple(self):
        # GIVEN
        given_headers = ["A", "B", "C"]
        given_rows = ["a", "b", "c"]

        # WHEN
        new_rows, new_headers = tabulate_color._rst_escape_first_column(given_rows, given_headers)

        # THEN
        self.assertListEqual(['A', 'B', 'C'], new_headers)
        self.assertListEqual([['a'], ['b'], ['c']], new_rows)

