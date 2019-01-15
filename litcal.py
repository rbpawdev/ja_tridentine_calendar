"""Generate a liturgical calendar using the 1962 Roman Catholic rubrics."""

import argparse
import calendar
import datetime as dt
import json
import os

import ics
from arrow import Arrow

FIXED_FEASTS_FNAME = 'fixed_feasts_ferias_et_al.json'
MOVABLE_FEASTS_FNAME = 'movable_feasts_ferias_et_al.json'
SEASONS_FNAME = 'seasons.json'

ORDINALS = {
    1: 'First',
    2: 'Second',
    3: 'Third',
    4: 'Fourth',
    5: 'Fifth',
    6: 'Sixth',
    7: 'Seventh',
    8: 'Eighth',
    9: 'Ninth',
    10: 'Tenth',
    11: 'Eleventh',
    12: 'Twelfth',
    13: 'Thirteenth',
    14: 'Fourteenth',
    15: 'Fifteenth',
    16: 'Sixteenth',
    17: 'Seventeenth',
    18: 'Eighteenth',
    19: 'Nineteenth',
    20: 'Twentieth',
    21: 'Twenty-first',
    22: 'Twenty-second',
    23: 'Twenty-third',
    24: 'Twenty-fourth',
    25: 'Twenty-fifth',
    26: 'Twenty-sixth',
    27: 'Twenty-seventh',
}


def get_args():
    """Define the command line arguments."""
    parser = argparse.ArgumentParser(description='Calculate a liturgical calendar.')
    parser.add_argument('--year', type=int, help='The year for which to calculate the calendar.')
    parser.add_argument('--file', help='Name of the ICS file to write the calendar to.')
    return parser.parse_args()


class LiturgicalCalendar(object):
    """A liturgical calendar following the 1962 Roman Catholic rubrics."""

    def __init__(self, year):
        """Instantiate a `LiturgicalCalendar` object.

        Note that the liturgical year starts before the year given on the first Sunday of Advent.
        If the year given is 2000, then the liturgical year will start in late November 1999 and end
        in early December 2000.

        Args:
            year: int
                The liturgical year to calculate the calendar for.

        """
        self.year = year
        self.dirname = os.path.dirname(os.path.realpath(__file__))
        
        with open(os.path.join(self.dirname, MOVABLE_FEASTS_FNAME)) as json_file:
            self.movable_feasts = json.load(json_file)

        with open(os.path.join(self.dirname, FIXED_FEASTS_FNAME)) as json_file:
            self.fixed_feasts = json.load(json_file)

        with open(os.path.join(self.dirname, SEASONS_FNAME)) as json_file:
            self.seasons = json.load(json_file)

        self.easter_date = computus(self.year)
        self.xmas = dt.date(self.year - 1, 12, 25)
        self.liturgical_year_start = self.xmas - dt.timedelta(self.xmas.weekday() + 22)
        next_xmas = dt.date(self.year, 12, 25)
        self.liturgical_year_end = next_xmas - dt.timedelta(next_xmas.weekday() + 23)

        self.calendar = {}
        date = self.liturgical_year_start
        while date <= self.liturgical_year_end:
            self.calendar[date] = []
            date += dt.timedelta(1)

        # First we mark fixed solemnities.
        date = self.liturgical_year_start
        while date <= self.liturgical_year_end:
            date_str = date.strftime('%B %-d')
            if date_str in self.fixed_feasts:
                for elem in self.fixed_feasts[date_str]:
                    if 'class' in elem and elem['class'] == 1:
                        self.calendar[date] += [elem]
            date += dt.timedelta(1)

        # Now the movable solemnities.
        function_name_pairs = (
            (self.gaudete_sunday_date, 'Gaudete Sunday'),
            (self.advent_embertide_dates, 'Advent Embertide'),
            (self.holy_name_date, 'Feast of the Holy Name'),
            (self.holy_family_date, 'Feast of the Holy Family'),
            (self.plough_monday_date, 'Plough Monday'),
            (self.septuagesima_date, 'Septuagesima'),
            (self.sexagesima_date, 'Sexagesima'),
            (self.quinquagesima_date, 'Quinquagesima'),
            (self.fat_thursday_date, 'Fat Thursday'),
            (self.shrove_monday_date, 'Shrove Monday'),
            (self.mardi_gras_date, 'Mardi Gras'),
            (self.ash_wednesday_date, 'Ash Wednesday'),
            (self.lenten_embertide_dates, 'Lenten Embertide'),
            (self.st_matthias_date, 'St. Matthias'),
            (self.st_gabriel_of_our_lady_of_sorrows_date, 'St. Gabriel of Our Lady of Sorrows'),
            (self.laetare_sunday_date, 'Laetare Sunday'),
            (self.passion_sunday_date, 'Passion Sunday'),
            (self.seven_sorrows_date, 'The Seven Sorrows'),
            (self.palm_sunday_date, 'Palm Sunday'),
            (self.palm_sunday_date + dt.timedelta(1), 'Monday of Holy Week'),
            (self.palm_sunday_date + dt.timedelta(2), 'Tuesday of Holy Week'),
            (self.palm_sunday_date, 'Palm Sunday'),
            (self.spy_wednesday_date, 'Spy Wednesday'),
            (self.maundy_thursday_date, 'Maundy Thursday'),
            (self.good_friday_date, 'Good Friday'),
            (self.holy_saturday_date, 'Holy Saturday'),
            (self.easter_date, 'Easter'),
            (self.easter_date + dt.timedelta(1), 'Easter Monday'),
            (self.easter_date + dt.timedelta(2), 'Easter Tuesday'),
            (self.easter_date + dt.timedelta(3), 'Easter Wednesday'),
            (self.easter_date + dt.timedelta(4), 'Easter Thursday'),
            (self.easter_date + dt.timedelta(5), 'Easter Friday'),
            (self.easter_date + dt.timedelta(6), 'Easter Saturday'),
            (self.quasimodo_sunday_date, 'Quasimodo Sunday'),
            (self.jubilate_sunday_date, 'Jubilate Sunday'),
            (self.misericordia_sunday_date, 'Misericordia Sunday'),
            (self.cantate_sunday_date, 'Cantate Sunday'),
            (self.major_rogation_date, 'Major Rogation'),
            (self.ascension_date, 'Ascension'),
            (self.minor_rogation_dates, 'Minor Rogation'),
            (self.pentecost_date, 'Pentecost'),
            (self.whit_embertide_dates, 'Whit Embertide'),
            (self.trinity_sunday_date, 'Trinity Sunday'),
            (self.corpus_christi_date, 'Corpus Christi'),
            (self.sacred_heart_date, 'Feast of the Sacred Heart'),
            (self.peters_pence_date, 'Peter\'s Pence'),
            (self.michaelmas_embertide_dates, 'Michaelmas Embertide'),
            (self.christ_the_king_date, 'Christ the King'),
        )

        for date_fn, name in function_name_pairs:
            if type(date_fn) is list:
                for elem in date_fn:
                    self.calendar[elem] += [self.movable_feasts[name]]
                    self.calendar[elem][-1]['name'] = name
            else:
                self.calendar[date_fn] += [self.movable_feasts[name]]
                self.calendar[date_fn][-1]['name'] = name

        # Mark Sundays, starting with Advent
        for i in range(1, 5):
            if i == 3:
                continue
            date = self.xmas - dt.timedelta(self.xmas.weekday() + 22 - 7 * (i - 1))
            self.calendar[date] += [{
                'name': ORDINALS[i] + ' Sunday of Advent',
                'liturgical_event': True,
            }]

        # Time after Epiphany.
        i = 2
        date = self.holy_family_date + dt.timedelta(7)
        while date < self.septuagesima_date:
            self.calendar[date] += [{
                'name': ORDINALS[i] + ' Sunday after Epiphany',
                'liturgical_event': True,
            }]
            i += 1
            date += dt.timedelta(7)

        # Lent.
        for i in range(1, 4):
            date = self.quinquagesima_date + dt.timedelta(7 * i)
            self.calendar[date] += [{
                'name': ORDINALS[i] + ' Sunday of Lent',
                'liturgical_event': True,
            }]

        # Eastertide.
        self.calendar[self.cantate_sunday_date + dt.timedelta(7)] += [{
            'name': 'Sunday after Ascension',
            'liturgical_event': True,
        }]

        # Time after Pentecost.
        i = 2
        date = self.trinity_sunday_date + dt.timedelta(7)
        while date <= self.liturgical_year_end - dt.timedelta(7):
            self.calendar[date] += [{
                'name': ORDINALS[i] + ' Sunday after Pentecost',
                'liturgical_event': True,
            }]
            i += 1
            date += dt.timedelta(7)
        self.calendar[date] += [{
            'name': 'Last Sunday after Pentecost',
            'liturgical_event': True,
        }]

        # Then second class fixed feasts or lower.
        date = self.liturgical_year_start
        while date <= self.liturgical_year_end:
            date_str = date.strftime('%B %-d')
            if date_str in self.fixed_feasts:
                for elem in self.fixed_feasts[date_str]:
                    if elem.get('class') != 1:
                        self.calendar[date] += [elem]
            date += dt.timedelta(1)

        self._add_seasons()

    def _add_seasons(self):
        date = self.liturgical_year_start
        while date <= self.liturgical_year_end:
            if date in [self.fat_thursday_date, self.shrove_monday_date, self.mardi_gras_date]:
                season_key = 'Shrovetide'
            elif self.liturgical_year_start <= date < dt.date(self.year - 1, 12, 25):
                season_key = 'Advent'
            elif dt.date(self.year - 1, 12, 25) <= date < dt.date(self.year, 1, 6):
                season_key = 'Christmastide'
            elif dt.date(self.year, 1, 6) <= date < self.septuagesima_date:
                season_key = 'Time after Epiphany'
            elif self.septuagesima_date <= date < self.ash_wednesday_date:
                season_key = 'Septuagesima'
            elif self.ash_wednesday_date <= date < self.passion_sunday_date:
                season_key = 'Lent'
            elif self.passion_sunday_date <= date < self.palm_sunday_date:
                season_key = 'Passiontide'
            elif self.palm_sunday_date <= date < self.maundy_thursday_date:
                season_key = 'Holy Week'
            elif self.maundy_thursday_date <= date < self.easter_date:
                season_key = 'Paschal Triduum'
            elif self.easter_date <= date < self.pentecost_date:
                season_key = 'Eastertide'
            elif self.pentecost_date <= date < dt.date(self.year, 10, 31):
                season_key = 'Time after Pentecost'
            elif dt.date(self.year, 10, 31) <= date < dt.date(self.year, 11, 3):
                season_key = 'Hallowtide'
            elif dt.date(self.year, 11, 3) <= date <= self.liturgical_year_end:
                season_key = 'Time after Pentecost'
            else:
                raise RuntimeError(
                    'date {} exceeded liturgical year range of {} to {}.'.format(
                        self.liturgical_year_start, self.liturgical_year_end))

            for i, elem in enumerate(self.calendar[date]):
                self.calendar[date][i]['season'] = self.seasons[season_key]
                self.calendar[date][i]['season'].update({'name': season_key})

            date += dt.timedelta(1)

    def __getitem__(self, key):
        return self.calendar[key]

    def _format_urls(self, event, format_html=False):
        description = ''
        if 'urls' in event:
            description += 'More information about {}:\n'.format(
                self._name_with_article(event))
            if format_html:
                description += '<ul>'
            for url_obj in event['urls']:
                if type(url_obj) is str:
                    if format_html:
                        description += '<li>' + url_obj + '</li>'
                    else:
                        description += '• ' + url_obj + '\n'
                elif type(url_obj) is dict:
                    if format_html:
                        description += '<li>' + url_obj['url'] + '</li>'
                    else:
                        description += '• ' + url_obj['url'] + '\n'
            if format_html:
                description += '</ul>'

        if 'season' in event:
            if 'urls' in event:
                description += '\n'
            if format_html:
                description += '<ul>'
            description += 'More information about {}:\n'.format(
                self._season_with_article(event['season']['name']))
            for url_obj in event['season']['urls']:
                if type(url_obj) is str:
                    if format_html:
                        description += '<li>' + url_obj + '</li>'
                    else:
                        description += '• ' + url_obj + '\n'
                elif type(url_obj) is dict:
                    description += '• ' + url_obj['url'] + '\n'
            if format_html:
                description += '</ul>'

        return description

    def _name_with_article(self, event):
        name = event['name']
        the_feast_of_prefixes = ['St.', 'SS.', 'Pope', 'Our Lady', 'Basilica']
        if any([name.startswith(elem) for elem in the_feast_of_prefixes]):
            if event.get('class') != 4:
                return 'the Feast of ' + name
            else:
                return 'the Commemoration of ' + name
        elif (name.split()[0] in ORDINALS.values() or
              name.startswith('Last Sunday') or
              name.startswith('Feast')):
            return 'the ' + name
        else:
            return name

    def _season_with_article(self, name):
        if name.startswith('Time after'):
            return 'the ' + name
        else:
            return name

    def to_ics(self):
        """Write out the calendar to ICS format."""
        ics_calendar = ics.Calendar()
        date = self.liturgical_year_start
        while date <= self.liturgical_year_end:
            for i, elem in enumerate(self.calendar[date]):
                ics_name = elem['name']
                name_with_article = self._name_with_article(elem)
                description = ''

                if elem.get('obligation'):
                    description += 'Today is a Holy Day of Obligation.\n\n'
                
                if not elem.get('liturgical_event'):
                    capitalized_name_with_article = (
                        name_with_article[0].upper() + name_with_article[1:])
                    description += '{} has no special liturgy.\n\n'.format(
                        capitalized_name_with_article)

                if i > 0 and elem.get('liturgical_event'):
                    outranking_feast = self.calendar[date][0]
                    ics_name = '« ' + ics_name + ' »'
                    if (outranking_feast['name'] in self.movable_feasts or
                        elem['name'] in self.movable_feasts or
                        'Sunday' in outranking_feast['name']):
                        description += 'This year {} is outranked by {}.\n\n'.format(
                            name_with_article, self._name_with_article(outranking_feast))
                    else:
                        description += '{} is outranked by {}.\n\n'.format(
                            name_with_article[0].upper() + name_with_article[1:],
                            self._name_with_article(outranking_feast))

                description += self._format_urls(elem, format_html=False)
                arrow_date = Arrow.fromdate(date)
                ics_event = ics.Event(name=ics_name, begin=arrow_date, description=description)
                ics_event.make_all_day()
                ics_calendar.events.add(ics_event)
            date += dt.timedelta(1)
        return ics_calendar


if __name__ == '__main__':
    args = get_args()
    litcal = LiturgicalCalendar(args.year)
    with open(args.file, 'w') as f:
        f.writelines(litcal.to_ics())
