from rake_nltk import Rake
import nltk

# nltk.download('punkt_tab')
# nltk.download('stopwords')
rake_nltk_var = Rake()

def getKeyWords(text):
    rake_nltk_var.extract_keywords_from_text(text)  
    return rake_nltk_var.get_ranked_phrases()