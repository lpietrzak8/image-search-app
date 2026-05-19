import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pytest
from unittest.mock import patch
from key_words import getKeyWords


def test_get_keywords_returns_list():
    result = getKeyWords("beautiful sunset over the ocean")
    assert isinstance(result, list)


def test_get_keywords_calls_extract_on_text():
    import key_words as kw_module
    with patch.object(kw_module.rake_nltk_var, 'extract_keywords_from_text') as mock_extract, \
         patch.object(kw_module.rake_nltk_var, 'get_ranked_phrases', return_value=['sunset', 'ocean']):
        result = getKeyWords("sunset over the ocean")
    mock_extract.assert_called_once_with("sunset over the ocean")
    assert result == ['sunset', 'ocean']


def test_get_keywords_returns_ranked_phrases():
    import key_words as kw_module
    with patch.object(kw_module.rake_nltk_var, 'extract_keywords_from_text'), \
         patch.object(kw_module.rake_nltk_var, 'get_ranked_phrases', return_value=['red car', 'mountain road']):
        result = getKeyWords("red car on mountain road")
    assert result == ['red car', 'mountain road']


def test_get_keywords_empty_returns_empty_list():
    import key_words as kw_module
    with patch.object(kw_module.rake_nltk_var, 'extract_keywords_from_text'), \
         patch.object(kw_module.rake_nltk_var, 'get_ranked_phrases', return_value=[]):
        result = getKeyWords("")
    assert result == []


def test_get_keywords_single_keyword():
    import key_words as kw_module
    with patch.object(kw_module.rake_nltk_var, 'extract_keywords_from_text'), \
         patch.object(kw_module.rake_nltk_var, 'get_ranked_phrases', return_value=['dog']):
        result = getKeyWords("dog")
    assert result == ['dog']


def test_get_keywords_multiple_phrases():
    import key_words as kw_module
    expected = ['golden retriever', 'green park', 'blue lake']
    with patch.object(kw_module.rake_nltk_var, 'extract_keywords_from_text'), \
         patch.object(kw_module.rake_nltk_var, 'get_ranked_phrases', return_value=expected):
        result = getKeyWords("golden retriever running in green park near blue lake")
    assert len(result) == 3
