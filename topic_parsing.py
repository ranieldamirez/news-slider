# topics_parsing.py

from flask import Blueprint, jsonify, request
import string
from collections import defaultdict, Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from models import Headline, NewsSource
from models import db  # adjust import based on your project structure

bp = Blueprint('topic_parsing', __name__)

# Ensure NLTK stopwords are downloaded; you might run this once in your setup.
import nltk
nltk.download('punkt')
nltk.download('stopwords')

STOPWORDS = set(stopwords.words('english'))

def bucket_bias(bias_score):
    """Categorize a bias score into a bias bucket."""
    if bias_score <= -6:
        return 'Strongly Left'
    elif bias_score <= -2:
        return 'Lean Left'
    elif bias_score <= 1:
        return 'Centrist'
    elif bias_score <= 5:
        return 'Lean Right'
    else:
        return 'Strongly Right'

def extract_topics():
    """
    Extract topics from current headlines.
    Only include tokens that are proper nouns (NNP/NNPS), appear in at least 3 different bias buckets,
    and occur at least 3 times overall.
    Additionally, filter out common noise words.
    """
    import nltk
    nltk.download('averaged_perceptron_tagger', quiet=True)
    
    headlines = Headline.query.all()
    token_buckets = defaultdict(set)
    token_frequency = Counter()

    # List of common noise words to ignore (in lowercase)
    noise_words = {"new", "news", "over", "could", "says", "today", "say", "last", "would", "Out", "City", "Him", "Most", "How", "First"}

    for headline in headlines:
        # Tokenize while preserving original capitalization for proper tagging
        tokens = word_tokenize(headline.title)
        tagged_tokens = nltk.pos_tag(tokens)
        # Filter tokens: proper noun, alphabetic, longer than 2 characters, not a noise word
        proper_tokens = [
            token for token, tag in tagged_tokens
            if tag in ("NNP", "NNPS") 
               and token.isalpha() 
               and len(token) > 2 
               and token.lower() not in noise_words
        ]
        
        source = NewsSource.query.get(headline.source_id)
        if not source:
            continue
        bucket = bucket_bias(source.bias_score)
        for token in set(proper_tokens):
            token_buckets[token].add(bucket)
        token_frequency.update(proper_tokens)

    topics = []
    for token, buckets in token_buckets.items():
        if len(buckets) >= 3 and token_frequency[token] >= 3:
            topics.append(token)
    
    topics = sorted(topics, key=lambda t: token_frequency[t], reverse=True)
    if not topics:
        topics = ["Miscellaneous"]

    return topics



@bp.route('/topics', methods=['GET'])
def get_topics():
    """Endpoint to return the dynamically extracted topics."""
    topics = extract_topics()  # This returns a sorted list of tokens.
    if len(topics) > 15:
        popular = topics[:15]
        popular.append("Misc")
    else:
        popular = topics
    return jsonify(popular)

