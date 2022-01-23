import argparse
import csv
import html
import pathlib

from bs4 import BeautifulSoup
import pandas as pd


def process_kml_file(kml_file_path: pathlib.Path):
    tables = _load_tables(kml_file_path)

    kml_file_dir = kml_file_path.parent

    cleaned_table = _index_by_block_id(tables)

    town_entries = cleaned_table['Town'].unique()
    if len(town_entries) != 1:
        raise RuntimeError(f'found the following towns in data: {town_entries}')
    town = town_entries[0]

    save_raw_tables_to_csv(tables, kml_file_dir / f'{town}_raw_tables.csv')
    save_cleaned_table(cleaned_table, kml_file_dir / f'{town}_by_block_id.csv')


def _extract_html_table(html_string):
    # The information we need in the KML file seems to be embedded
    # within it as HTML tables.  We create a separate HTML parser
    # to read data from the tables.
    soup = BeautifulSoup(html_string, 'lxml')

    tables = soup.find_all('table')
    assert len(tables) == 2, len(tables)

    title = _get_title_from_first_table(tables[0])

    relevant_table = tables[1]

    return title, _parse_table(relevant_table)


def _get_title_from_first_table(table):
    first_row_columns = table.tr.find_all('td')
    assert len(first_row_columns) == 1, len(first_row_columns)
    return first_row_columns[0].text


def _parse_table(table):
    data = {}
    for row in table.find_all('tr'):
        columns = row.find_all('td')
        assert len(columns) == 2
        key, value = columns
        assert key not in data
        data[key.text] = value.text

    return data


def _load_tables(kml_file_path: pathlib.Path):
    with open(kml_file_path) as f:
        s = BeautifulSoup(f, 'xml')
        tables = []
        for placemark in s.find_all('Placemark'):
            placemark_description = placemark.description.text
            title, table = _extract_html_table(placemark_description)
            tables.append((title, table))

    return tables


def _index_by_block_id(tables):
    fields = get_fields()
    info_by_block_id = {}
    for title, table in tables:
        block_id_field = 'Block Group Identification Number'
        if block_id_field not in table:
            continue

        block_id = table[block_id_field]
        if block_id not in info_by_block_id:
            info_by_block_id[block_id] = {field: None for field in fields}
        this_group = info_by_block_id[block_id]
        table_with_block_group = {**table, **{'Block Group': title}}
        for key, value in table_with_block_group.items():
            if key in fields:
                if this_group[key] is None:
                    this_group[key] = value
                else:
                    assert this_group[key] == value, \
                        f'value of {key} differed in {block_id}: {this_group[key]} vs. {value}'

    df = pd.DataFrame.from_dict(info_by_block_id, orient='index', columns=fields)
    df.index.name = block_id_field
    return df


def save_cleaned_table(cleaned_table, output_path):
    cleaned_table.to_csv(output_path)


def save_raw_tables_to_csv(tables, output_path):
    with open(output_path, 'w') as csvfile:
        for title, table in tables:
            writer = csv.writer(csvfile)
            writer.writerow([title, ''])
            for key, value in table.items():
                writer.writerow([key, value])

            writer.writerow(['', ''])


def get_fields():
    return (
        'Block Group',
        'Town',
        'Active Electric Locations, 2019',
        'Active Electric Accounts as of December, 2019',
        '2013 Electric Location Participation Rate',
        '2014 Electric Location Participation Rate',
        '2015 Electric Location Participation Rate',
        '2016 Electric Location Participation Rate',
        '2017 Electric Location Participation Rate',
        '2018 Electric Location Participation Rate',
        '2019 Electric Location Participation Rate',
        '2013-2019 Total Electric Location Participation Rate',
        '2013-2019 Total Electric Location Participation Rate Rank',
        '2013-2019 Electric location participation rate percentage points difference from town mean',
        'Active Gas Locations, 2019',
        'Active Gas Accounts as of December, 2019',
        '2013 Gas Location Participation Rate',
        '2014 Gas Location Participation Rate',
        '2015 Gas Location Participation Rate',
        '2016 Gas Location Participation Rate',
        '2017 Gas Location Participation Rate',
        '2018 Gas Location Participation Rate',
        '2019 Gas Location Participation Rate',
        '2013-2019 Total Gas Location Participation Rate',
        '2013-2019 Total Gas Location Participation Rate Rank',
        '2013-2019 Gas location participation rate percentage points difference from town mean',
        '2018 Block Group rank ordered by share of income eligible households',
        '2018 ACS Share of income eligible households',
        '2018 Block Group rank ordered by share of renter occupied households',
        '2018 ACS Share of renter occupied households',
        '2018 Block Group rank ordered by share of limited english proficiency households',
        '2018 ACS Share of limited english proficiency households',
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            'Extract information from a certain type of KML file, '
            'and save it into CSV files.'
        ),
    )
    parser.add_argument(
        '--kml_path',
        type=pathlib.Path,
        required=True,
        help='path to kml file (typically called \'doc.kml\')',
    )

    args = parser.parse_args()
    process_kml_file(args.kml_path)
