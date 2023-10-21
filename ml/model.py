import os

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, TfidfTransformer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from scipy.sparse import vstack
from ml import config


class ModelBuilder:
    def __init__(self, categories_file_path, root_folder_path, max_features):
        self._categories = config.read_categories_csv(categories_file_path)
        self._root_folder_path = root_folder_path
        self._vectorizer = TfidfVectorizer(max_features=max_features)
        self._classifier = MultinomialNB()

        print("downloading nltk data")
        nltk_data_path = "/tmp/nltk_data"
        nltk.data.path.append(nltk_data_path)
        nltk.download('stopwords', download_dir=nltk_data_path)
        nltk.download('punkt', download_dir=nltk_data_path)

    def build(self):
        print("computing vocabulary of words...")
        vocabulary = set()
        for (_, doc) in self._iterate_categories_docs():
            for word in doc.split():
                vocabulary.add(word)
        print(f"there are {len(vocabulary)} words in vocabulary ✓")

        print("running words count vectorizer on text corpus...")
        cv = CountVectorizer(vocabulary=vocabulary)
        docs_bows = []
        y = []
        for (category, doc) in self._iterate_categories_docs():
            docs_bows.append(cv.fit_transform([doc]))
            y.append(category['label'])
        print(f"transformed {len(docs_bows)} bags-of-words ✓")

        print("computing tf-idf vectors")
        x = vstack(docs_bows)
        x = TfidfTransformer().fit_transform(x)

        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)
        self.train_evaluate_model(x_train, x_test, y_train, y_test)

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
                                print(f"error while reading doc: {e}")

    def train_evaluate_model(self, x_train, x_test, y_train, y_test):
        print("training classifier model...")
        self._classifier.fit(x_train, y_train)
        print("classifier model trained ✓")

        # Evaluate the model
        y_predictions = self._classifier.predict(x_test)

        # Calculate accuracy and print the classification report and confusion matrix
        print("print classification report:\n---")
        print(classification_report(y_test, y_predictions))
        print("confusion matrix:")
        print(confusion_matrix(y_test, y_predictions))


def preprocess_text(text):
    # Tokenize the text
    words = word_tokenize(text)

    # Remove stopwords
    words = [word.lower() for word in words if word.isalnum() and word.lower() not in stopwords.words('english')]

    # Perform stemming or lemmatization here if needed

    # Rejoin the words into a cleaned text
    cleaned_text = ' '.join(words)

    return cleaned_text
