import logging

from model import config
from model.persistence import load_model


class ModelReader:
    def __init__(self, categories_file_path, root_folder_path):
        self._classifier, self._vectorizer, self._transformer = load_model(root_folder_path)
        self._categories = {}
        for category in config.read_categories_csv(categories_file_path):
            self._categories[category['label']] = {
                'label': category['label'],
                'name': category['name'],
                'description': category['description']
            }

    def classify(self, text):
        if self._classifier is None:
            logging.error("model not loaded")
            return None
        count_vector = self._vectorizer.transform([text])
        tfidf_vector = self._transformer.transform(count_vector)
        prediction = self._classifier.predict(tfidf_vector)
        category = prediction[0]
        if category in self._categories:
            return self._categories[category]
        return {
            'label': category,
            'name': category
        }
