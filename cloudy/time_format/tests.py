from django.test import TestCase

from cloudy.time_format.formatters import HhmmFormatter, TenthFormatter


class HhmmFormatterTest(TestCase):
    def test_output(self):
        self.assertEqual(HhmmFormatter.output(0), "0:00")
        self.assertEqual(HhmmFormatter.output(5), "0:05")
        self.assertEqual(HhmmFormatter.output(11), "0:11")
        self.assertEqual(HhmmFormatter.output(60), "1:00")

    def test_input(self):
        self.assertEqual(HhmmFormatter.input("0:00"), 0)
        self.assertEqual(HhmmFormatter.input("0:0"), 0)
        self.assertEqual(HhmmFormatter.input("0:05"), 5)
        self.assertEqual(HhmmFormatter.input("0:11"), 11)
        self.assertEqual(HhmmFormatter.input("1:00"), 60)


class TenthFormatterTest(TestCase):
    def test_output(self):
        self.assertEqual(TenthFormatter.output(56), "0.9")
        self.assertEqual(TenthFormatter.output(57), "1.0")
        self.assertEqual(TenthFormatter.output(0), "0.0")
        self.assertEqual(TenthFormatter.output(65), "1.1")
        self.assertEqual(TenthFormatter.output(68), "1.1")

    def test_input(self):
        self.assertEqual(TenthFormatter.input("0.9"), 54)
        self.assertEqual(TenthFormatter.input("1.0"), 60)
        self.assertEqual(TenthFormatter.input("0.6"), 36)
        self.assertEqual(TenthFormatter.input("1.1"), 66)


class CanadianFormatterTest(TestCase):
    def test_output(self):
        pass

    def test_input(self):
        pass
