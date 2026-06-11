import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

_stopwords_mock = MagicMock()
_stopwords_mock.words.return_value = ["the", "a", "an", "is", "in", "on", "of", "and", "or", "to"]

_nltk_corpus_mock = MagicMock()
_nltk_corpus_mock.stopwords = _stopwords_mock

_nltk_mock = MagicMock()
_nltk_mock.corpus = _nltk_corpus_mock

_rake_instance = MagicMock()
_rake_instance.get_ranked_phrases.return_value = []

_rake_nltk_mock = MagicMock()
_rake_nltk_mock.Rake.return_value = _rake_instance

sys.modules.setdefault('nltk', _nltk_mock)
sys.modules.setdefault('nltk.corpus', _nltk_corpus_mock)
sys.modules.setdefault('rake_nltk', _rake_nltk_mock)
