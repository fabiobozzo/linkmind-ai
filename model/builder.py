import logging
import os
import string

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from scipy.sparse import vstack
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.naive_bayes import MultinomialNB
from tqdm import tqdm

from model import config
from model.persistence import store_model


class ModelBuilder:
    def __init__(self, categories_file_path, root_folder_path):
        self._categories = config.read_categories_csv(categories_file_path)
        self._root_folder_path = root_folder_path
        self._count_vectorizer = None  # must be created along with vocabulary from corpus
        self._tfidf_transformer = TfidfTransformer()
        self._classifier = MultinomialNB()

        logging.info("downloading nltk data")
        nltk_data_path = "/tmp/nltk_data"
        nltk.data.path.append(nltk_data_path)
        nltk.download('stopwords', download_dir=nltk_data_path)
        nltk.download('punkt', download_dir=nltk_data_path)

    def build(self):
        try:
            x, y = self.vectorize_text_corpus()
            x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)
            self.train_evaluate_model(x_train, x_test, y_train, y_test)
            store_model(
                self._root_folder_path,
                self._classifier,
                self._count_vectorizer,
                self._tfidf_transformer
            )
        except Exception as e:
            logging.error(f"error while building classifier model", e, exc_info=True)

    def _iterate_categories_docs(self):
        for category in self._categories:
            category_path = os.path.join(self._root_folder_path, category['label'])
            if os.path.exists(category_path):
                for root, dirs, files in os.walk(category_path):
                    for filename in files:
                        if not str(filename).endswith('.json'):
                            file_path = os.path.join(root, filename)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as file:
                                    yield category, preprocess_text(file.read())
                            except OSError as e:
                                logging.error(f"error while reading doc file", e, exc_info=True)

    def vectorize_text_corpus(self):
        logging.info("collecting vocabulary of words...")
        vocabulary = set()
        docs_count = 0
        for (_, doc) in self._iterate_categories_docs():
            docs_count += 1
            for word in doc.split():
                vocabulary.add(word)
        logging.info(f"there are {len(vocabulary)} words in vocabulary ✓")

        logging.info("computing bag-of-words vectors with count vectorizer...")
        self._count_vectorizer = CountVectorizer(vocabulary=vocabulary)
        cv_pb = tqdm(total=docs_count, desc="Processing", bar_format='{l_bar}{bar}', position=0)
        docs_bows = []
        y = []
        for (category, doc) in self._iterate_categories_docs():
            docs_bows.append(self._count_vectorizer.fit_transform([doc]))
            y.append(category['label'])
            cv_pb.update(1)
        logging.info(f"{len(docs_bows)} bags-of-words computed ✓")

        logging.info("transform bow vectors into tf-idf")
        x = vstack(docs_bows)
        x = self._tfidf_transformer.fit_transform(x)
        logging.info("tf-idf transformation complete ✓")

        return x, y

    def train_evaluate_model(self, x_train, x_test, y_train, y_test):
        logging.info("optimizing hyperparameters...")
        param_grid = {
            'alpha': [0.1, 0.5, 1.0, 2.0],
            'fit_prior': [True, False]
        }
        gs = GridSearchCV(self._classifier, param_grid, cv=5)
        gs.fit(x_train, y_train)
        best_alpha = gs.best_params_['alpha']
        best_fit_prior = gs.best_params_['fit_prior']
        logging.info("hyperparameters optimized with grid search ✓")
        logging.debug(gs.best_params_)

        logging.info("training classifier model...")
        self._classifier = MultinomialNB(alpha=best_alpha, fit_prior=best_fit_prior)
        self._classifier.fit(x_train, y_train)
        logging.info("classifier model trained ✓")

        # Evaluate the model
        y_predictions = self._classifier.predict(x_test)

        # Print the classification report and confusion matrix
        logging.info("print classification report:\n---")
        print(classification_report(y_test, y_predictions))
        # logging.info("confusion matrix:")
        # print(confusion_matrix(y_test, y_predictions))


def preprocess_text(text):
    # check characters to see if they are in punctuation
    nopunc = [char for char in text if char not in string.punctuation]
    nopunc = ''.join(nopunc)
    # Tokenize the text
    words = word_tokenize(nopunc)
    # Remove stopwords
    words = [word.lower() for word in words if
             word.isascii() and (not word.isnumeric()) and word.lower() not in stopwords.words('english')]
    # TODO: Perform stemming or lemmatization here if needed
    # Rejoin the words into a cleaned text
    return ' '.join(words)
