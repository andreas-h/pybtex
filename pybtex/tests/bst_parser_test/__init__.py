import pkgutil

from pybtex.bibtex import bst
from io import StringIO



test_data = (
    'plain',
    'apacite',
    'jurabib',
)


def check_bst_parser(dataset_name):
    module = __import__('pybtex.tests.bst_parser_test.{0}'.format(dataset_name), globals(), locals(), 'bst')
    correct_result = module.bst
    bst_data = pkgutil.get_data('pybtex.tests.bst_parser_test', dataset_name + '.bst').decode('latin1')
    actual_result = list(bst.parse_stream(StringIO(bst_data)))

    # XXX pyparsing return list-like object which are not equal to plain lists
    for correct_element, actual_element in zip(actual_result, correct_result):
        assert repr(correct_element) == repr(actual_element), '\n{0}\n{1}'.format(correct_element, actual_element)

 
def test_bst_parser():
    for dataset_name in test_data:
        yield check_bst_parser, dataset_name
