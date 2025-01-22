from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib
import os

class MLCategorizer:
    def __init__(self, model_path='ml_models'):
        self.model_path = model_path
        self.model_file = os.path.join(model_path, 'transaction_categorizer.joblib')
        self.pipeline = None
        self.fallback_rules = {
            'Food': ['starbucks', 'mcdonald', 'restaurant', 'cafe', 'doordash', 'uber eats'],
            'Entertainment': ['netflix', 'spotify', 'playstation', 'google *youtube', 'hulu', 'disney+'],
            'Shopping': ['amazon', 'target', 'walmart', 'ebay', 'costco', 'bestbuy'],
            'Transportation': ['uber', 'lyft', 'chevron', 'gas', 'shell', 'exxon'],
            'Utilities': ['comcast', 'verizon', 'electric', 'water', 'pg&e', 'at&t'],
            'Healthcare': ['pharmacy', 'doctor', 'medical', 'hospital', 'dental'],
            'Housing': ['rent', 'mortgage', 'hoa', 'maintenance'],
            'Education': ['tuition', 'books', 'school', 'university'],
        }
        
        # Initialize or load the model
        self._initialize_model()

    def _initialize_model(self):
        """Initialize or load the existing model"""
        if os.path.exists(self.model_file):
            self.pipeline = joblib.load(self.model_file)
        else:
            self.pipeline = Pipeline([
                ('vectorizer', TfidfVectorizer(ngram_range=(1, 2))),
                ('classifier', MultinomialNB())
            ])
            os.makedirs(self.model_path, exist_ok=True)

    def train(self, descriptions, categories):
        """Train the model with new data"""
        self.pipeline.fit(descriptions, categories)
        joblib.dump(self.pipeline, self.model_file)

    def predict(self, description):
        """Predict category for a given transaction description"""
        try:
            if self.pipeline and hasattr(self.pipeline, 'predict'):
                # Clean and normalize the description
                cleaned_description = description.lower().strip()
                prediction = self.pipeline.predict([cleaned_description])[0]
                confidence = max(self.pipeline.predict_proba([cleaned_description])[0])
                
                # If confidence is too low, fall back to rule-based system
                if confidence < 0.3:
                    return self._apply_fallback_rules(cleaned_description)
                return prediction
            else:
                return self._apply_fallback_rules(description.lower().strip())
        except Exception as e:
            print(f"ML prediction error: {str(e)}")
            return self._apply_fallback_rules(description.lower().strip())

    def _apply_fallback_rules(self, description):
        """Apply rule-based categorization as a fallback"""
        for category, keywords in self.fallback_rules.items():
            if any(keyword in description for keyword in keywords):
                return category
        return 'Other'

    def add_training_data(self, new_descriptions, new_categories):
        """Add new training data and retrain the model"""
        self.train(new_descriptions, new_categories)