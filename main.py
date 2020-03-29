import json
import lxml.html
import requests


class UnitStats:
    URL = "https://www.unitstatistics.com/age-of-empires2/"

    KEYS = [("name", str),
            ("type1", str),
            ("type2", str),
            ("building", str),
            ("age", str),
            ("food", int),
            ("wood", int),
            ("gold", int),
            ("total_cost", int),
            ("build_time", float),
            ("attack_speed", float),
            ("delay", float),
            ("movement_speed", float),
            ("line_of_sight", int),
            ("hp", int),
            ("range_min", float),
            ("range", float),
            ("damage", int),
            ("accuracy", float),
            ("armor_melee", int),
            ("armor_pierce", int)]

    def __init__(self, filepath=None):
        self.units = []

        if filepath is not None:
            with open(filepath, "r") as file:
                self.units = json.load(file)

    def save(self, filepath):
        with open(filepath, "w") as file:
            file.write(json.dumps(self.units, indent=2))

    @staticmethod
    def generate_key(unit_name):
        return unit_name.replace(' ', '_').lower()

    def fetch_remote(self):
        html_content = requests.get(UnitStats.URL).content

        root = lxml.html.fromstring(str(html_content))
        items = root.xpath("//tbody/tr")
        for item in items:
            unit = {}
            for i in range(0, len(UnitStats.KEYS)):
                unit[UnitStats.KEYS[i][0]] = self.try_parse(
                    str(item.xpath("td[{}]/text()".format(i + 1))[0]).strip(), UnitStats.KEYS[i][1])
                unit['key'] = self.generate_key(unit['name'])
            self.units.append(unit)

        return units

    def try_parse(self, value, value_type):
        if value_type == str:
            return str(value)

        if len(value) == 0 or value == '-':
            return None

        if value[-1] == '%':
            return float(value[:-1]) / 100.0

        return value_type(value)

    def get_unit(self, key):
        return [u for u in self.units if u['key'] == key][0]


class MediaWiki:
    pass

    @staticmethod
    def test_wiki_url(url):
        html_content = requests.get(url).content
        root = lxml.html.fromstring(str(html_content))
        return len(root.xpath("//table[@class='wikitable']")) > 0

    @staticmethod
    def determine_wiki_url(unit):
        unit_name_url = unit['name'].replace(" ", "_")

        base_url = "https://ageofempires.fandom.com/wiki/{}".format(unit_name_url)

        url_candidates = [base_url, base_url + "_(Age_of_Empires_II)"]

        for url in url_candidates:
            if MediaWiki.test_wiki_url(url):
                return url

        return None

    @staticmethod
    def scrape_links_or_text(root, xpath):
        elements = root.xpath(xpath + "/a/text()")
        if len(elements) > 0:
            return [str(v) for v in elements]

        return root.xpath(xpath + "/text()")

    @staticmethod
    def is_key_missing(unit, key):
        return key not in unit or type(unit[key]) == list and len(unit[key]) == 0 or unit[key] is None

    @staticmethod
    def any_key_missing(unit, keys):
        return any([MediaWiki.is_key_missing(unit, k) for k in keys])

    @staticmethod
    def fetch_details(unit):
        url = unit['wiki_url']

        required_keys = ['strong_against', 'weak_against']
        if MediaWiki.any_key_missing(unit, required_keys):
            html_content = requests.get(url).content
            root = lxml.html.fromstring(str(html_content))

            unit['strong_against'] = MediaWiki.scrape_links_or_text(root, "//table[@class='wikitable']/tr[2]/td[2]")
            unit['weak_against'] = MediaWiki.scrape_links_or_text(root, "//table[@class='wikitable']/tr[3]/td[2]")


if __name__ == "__main__":
    units = UnitStats('units.json')

    for unit in units.units:
        if unit['wiki_url'] is not None:
            print("Processing {}".format(unit['name']))
            MediaWiki.fetch_details(unit)
        else:
            print("Skipping {}".format(unit['name']))

    for unit in units.units:
        if unit['key'].startswith('elite'):
            base_unit = units.get_unit(unit['key'][6:])
            unit['weak_against'] = base_unit['weak_against']
            unit['strong_against'] = base_unit['strong_against']
    units.save('units.json')
