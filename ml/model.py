import logging
import os

import joblib
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from scipy.sparse import vstack
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from tqdm import tqdm

from ml import config


class ModelBuilder:
    def __init__(self, categories_file_path, root_folder_path, model_filename):
        self._categories = config.read_categories_csv(categories_file_path)
        self._root_folder_path = root_folder_path
        self._model_filename = model_filename

        logging.info("downloading nltk data")
        nltk_data_path = "/tmp/nltk_data"
        nltk.data.path.append(nltk_data_path)
        nltk.download('stopwords', download_dir=nltk_data_path)
        nltk.download('punkt', download_dir=nltk_data_path)

        if not self._model_filename == "":
            self._classifier = joblib.load(self._model_filename)
            logging.info("model loaded successfully ✓")
        else:
            self._classifier = MultinomialNB()
            logging.info("empty new model created")

    def build(self):
        logging.info("collecting vocabulary of words...")
        vocabulary = set()
        docs_count = 0
        for (_, doc) in self._iterate_categories_docs():
            docs_count += 1
            for word in doc.split():
                vocabulary.add(word.lower())
        logging.info(f"there are {len(vocabulary)} words in vocabulary ✓")

        logging.info("computing bags-of-words with count vectorizer...")
        cv = CountVectorizer(vocabulary=vocabulary)
        cv_pb = tqdm(total=docs_count, desc="Processing", bar_format='{l_bar}{bar}', position=0)
        docs_bows = []
        y = []
        for (category, doc) in self._iterate_categories_docs():
            docs_bows.append(cv.fit_transform([doc]))
            y.append(category['label'])
            cv_pb.update(1)
        logging.info(f"{len(docs_bows)} bags-of-words computed ✓")

        logging.info("transform count vectors into tf-idf")
        x = vstack(docs_bows)
        x = TfidfTransformer().fit_transform(x)
        logging.info("tf-idf transformation complete ✓")

        try:
            x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)
            self.train_evaluate_model(x_train, x_test, y_train, y_test)

            logging.info("storing model...")
            joblib.dump(self._classifier, self._model_filename)
            logging.info("model stored successfully ✓")
        except Exception as e:
            logging.error(f"error while training classifier model", e, exc_info=True)

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

    def train_evaluate_model(self, x_train, x_test, y_train, y_test):
        logging.info("training classifier model...")
        self._classifier.fit(x_train, y_train)
        logging.info("classifier model trained ✓")

        # Evaluate the model
        y_predictions = self._classifier.predict(x_test)

        # Calculate accuracy and print the classification report and confusion matrix
        logging.info("print classification report:\n---")
        print(classification_report(y_test, y_predictions))
        # logging.info("confusion matrix:")
        # print(confusion_matrix(y_test, y_predictions))


def preprocess_text(text):
    # Tokenize the text
    words = word_tokenize(text)
    # Remove stopwords
    words = [word.lower() for word in words if word.isalnum() and word.lower() not in stopwords.words('english')]
    # TODO: Perform stemming or lemmatization here if needed
    # Rejoin the words into a cleaned text
    return ' '.join(words)
