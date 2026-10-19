from django.test import TestCase

# Create your tests here.
"""
    quotes.tests
    ~~~~~~~~~~~~

    Ensure that all code runs as advertised.

    :author:    Randall Degges
    :email:     rdegges@gmail.com
    :license:   BSD, Randall Degges. Not covered by the AGPL at the repository root.
"""


from cloudy.quotes.models import Quote
from cloudy.quotes.templatetags.quotes_tags import show_quote, show_random_quote


class TemplateTagsTestCase(TestCase):
    """
    Tests the templatetags for proper functionality when reading from a
    populated `Quote` database.
    """

    fixtures = ["test_templatetags.json"]

    # Test constants dependent on fixtures.
    SHOW_QUOTE_PK = 1
    SHOW_QUOTE_AUTHOR = "Randall Degges"
    SHOW_QUOTE_QUOTE = "I am crazy."

    def test_show_quote(self):
        """
        Test to make sure that show_quote operates properly when given a valid
        `Quote` to display.
        """
        quote = show_quote(self.SHOW_QUOTE_PK)["quote"]
        self.assertEqual(quote.author, self.SHOW_QUOTE_AUTHOR)
        self.assertEqual(quote.quote, self.SHOW_QUOTE_QUOTE)

    def test_show_random_quote(self):
        """
        Test to make sure that `show_random_quote` operates properly when there
        are multiple `Quotes` in the database.
        """
        quote = show_random_quote()["quote"]
        self.assertTrue(quote)


class TemplateTagsEmptyTestCase(TestCase):
    """
    Tests the templatetags for proper functionality with no `Quote` fixture
    data, to see how they perform under race conditions.
    """

    def setUp(self):
        for x in Quote.objects.all():
            x.delete()

    def test_show_quote_non_existent(self):
        """
        Test to make sure that show_quote operates properly if the specified
        `Quote` is non-existent.
        """
        quote = show_quote(69)["quote"]
        self.assertFalse(quote)

    def test_show_random_quote_non_existent(self):
        """
        Test to make sure that `show_random_quote` operates properly when there
        are no `Quotes` in the database.
        """
        quote = show_random_quote()["quote"]
        self.assertFalse(quote)
