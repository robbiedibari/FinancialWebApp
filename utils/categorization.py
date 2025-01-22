from .ml_categorizer import MLCategorizer
import os

# Create a global categorizer instance
model_path = os.path.join(os.path.dirname(__file__), 'ml_models')
categorizer = MLCategorizer(model_path=model_path)

def categorize_transaction(description):
    """
    Categorize a transaction using ML-based categorization
    
    Args:
        description (str): Transaction description
        
    Returns:
        str: Predicted category
    """
    return categorizer.predict(description)

def train_categorizer(descriptions, categories):
    """
    Train the categorizer with new data
    
    Args:
        descriptions (list): List of transaction descriptions
        categories (list): List of corresponding categories
    """
    categorizer.train(descriptions, categories)
