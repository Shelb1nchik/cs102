import math
import string


class NaiveBayesClassifier:
    def __init__(self, alpha=1e-15):
        self.alpha = alpha
        self.classes = []
        self.class_word_counts = {}
        self.class_document_count = {}
        self.word_counts = {}
        self.total_documents = 0

    def fit(self, X, y):
        self.classes = list(set(y))
        self.total_documents = len(X)

        for c in self.classes:
            self.class_word_counts[c] = {}
            self.class_document_count[c] = 0

        for i in range(len(X)):
            document = X[i]
            target_class = y[i]

            self.class_document_count[target_class] += 1

            for word in self.tokenize(document):
                if word not in self.class_word_counts[target_class]:
                    self.class_word_counts[target_class][word] = 0
                if word not in self.word_counts:
                    self.word_counts[word] = 0

                self.class_word_counts[target_class][word] += 1
                self.word_counts[word] += 1

    def predict(self, X):
        predictions = []

        for document in X:
            class_scores = {}

            for c in self.classes:
                class_scores[c] = math.log(self.class_document_count[c] / self.total_documents)

                for word in self.tokenize(document):
                    class_scores[c] += math.log(
                        (self.class_word_counts[c].get(word, 0) + self.alpha)
                        / (self.word_counts.get(word, 0) + self.alpha * len(self.word_counts))
                    )

            predicted_class = max(class_scores, key=class_scores.get)
            predictions.append(predicted_class)

        return predictions

    def score(self, X_test, y_test):
        predictions = self.predict(X_test)
        correct_predictions = sum(1 for pred, true in zip(predictions, y_test) if pred == true)
        accuracy = correct_predictions / len(y_test)
        return accuracy

    @staticmethod
    def tokenize(text):
        translator = str.maketrans("", "", string.punctuation)
        text = text.lower().translate(translator)
        return text.split()
