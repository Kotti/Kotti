import re
from unidecode import unidecode

from pyramid.settings import asbool

from kotti import get_settings


# Define and compile static regexes
FILENAME_REGEX = re.compile(r"^(.+)\.(\w{,4})$", re.U)
IGNORE_REGEX = re.compile(r"['\"]", re.U)
URL_DANGEROUS_CHARS_REGEX = re.compile(r"[!#$%&()*+,/:;<=>?@\\^{|}\[\]~`]+",
                                       re.U)
MULTIPLE_DASHES_REGEX = re.compile(r"\-+", re.U)
EXTRA_DASHES_REGEX = re.compile(r"(^\-+)|(\-+$)", re.U)
# Define static constraints
MAX_LENGTH = 50
MAX_URL_LENGTH = 255


def crop_name(base, maxLength=MAX_LENGTH):
    baseLength = len(base)

    index = baseLength
    while index > maxLength:
        index = base.rfind('-', 0, index)

    if index == -1 and baseLength > maxLength:
        base = base[:maxLength]

    elif index > 0:
        base = base[:index]

    return base


def url_normalizer(text, locale=None, max_length=MAX_URL_LENGTH):

    key = 'kotti.url_normalizer.map_non_ascii_characters'
    map_non_ascii = asbool(get_settings()[key])
    if map_non_ascii:
        text = unidecode(text)

    # lowercase text
    base = text.lower()
    ext = ''

    m = FILENAME_REGEX.match(base)
    if m is not None:
        base = m.groups()[0]
        ext = m.groups()[1]

    base = base.replace(u' ', '-')
    base = IGNORE_REGEX.sub(u'', base)
    base = URL_DANGEROUS_CHARS_REGEX.sub(u'-', base)
    base = EXTRA_DASHES_REGEX.sub(u'', base)
    base = MULTIPLE_DASHES_REGEX.sub(u'-', base)

    base = crop_name(base, maxLength=max_length)

    if ext != '':
        base = base + u'.' + ext

    return base
