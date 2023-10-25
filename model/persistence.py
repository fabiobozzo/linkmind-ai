import logging
import os.path

import joblib

classifier_filename = 'classifier.pkl'
count_vectorizer_filename = 'count_vectorizer.pkl'
tfidf_transformer_filename = 'tfidf_transformer.pkl'
subfolder = '_dist'


def store_model(root_path, classifier, count_vectorizer, tfidf_transformer):
    logging.info("storing model...")
    joblib.dump(classifier, os.path.join(root_path, subfolder, classifier_filename))
    joblib.dump(count_vectorizer, os.path.join(root_path, subfolder, count_vectorizer_filename))
    joblib.dump(tfidf_transformer, os.path.join(root_path, subfolder, tfidf_transformer_filename))
    logging.info("model stored successfully ✓")


def load_model(root_path):
    logging.info("loading model...")
    classifier = joblib.load(os.path.join(root_path, subfolder, classifier_filename))
    count_vectorizer = joblib.load(os.path.join(root_path, subfolder, count_vectorizer_filename))
    tfidf_transformer = joblib.load(os.path.join(root_path, subfolder, tfidf_transformer_filename))
    logging.info("model loaded successfully ✓")
    return classifier, count_vectorizer, tfidf_transformer
