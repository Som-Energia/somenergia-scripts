import csv

def parse_csv(csv_file, filter):
    if not csv_file: return []
    with open(csv_file) as f:
        reader = csv.reader(f)
        for row in reader:
            item = filter(row[0])
            if not item: continue
            yield item


def parse_comma_separated_list(inputstring, filter):
    for item in inputstring.split(','):
        item = filter(item)
        if not item: continue
        yield item


def join_cli_and_csv(cli, csv_file, filter):
    return list(set(
        parse_csv(csv_file, filter)
    ).union(
        parse_comma_separated_list(cli, filter)
    ))

def contract_filter(item):
    """
    If it does not looks like a contract number
    returns empty string.
    Else it zeropads the number to canonicalize it.
    """
    CONTRACT_CODE_LENGTH=7
    def ignore():
        warn("Ignoring Contract '{}'", result)
        return ''
    result = item.strip()
    if not result.isdigit(): # equiv /[0-9]+/
        return ignore()
    if len(item)>CONTRACT_CODE_LENGTH:
        return ignore()
    return result.zfill(CONTRACT_CODE_LENGTH)

def cups_filter(item):
    result = item.strip()[:20]
    if len(result) != 20:
        warn("Ignoring CUPS '{}'".format(result))
        return ''
    return result

def mongo_profiles():
    """
    Maps commandline server ids to dbconfig
    mongo profile names.
    """
    return dict(
        erp01='prod',
        terp01='test',
        perp01='pre',
        serp01='stage',
    )

def mongo_profile(name):
    profiles = mongo_profiles()
    import configdb
    return configdb.mongodb_profiles[profiles[name]]




