import csv
from datetime import datetime
from models import Expense, Category, db
from .categorization import categorize_transaction, train_categorizer

def import_csv(file_path, user_id):
    """
    Imports transactions from a CSV file and saves them to the database.
    Also collects training data for the ML categorizer.
    """
    training_descriptions = []
    training_categories = []
    
    try:
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    # Extract necessary fields from the CSV row
                    description = row.get('Description', '').strip()
                    debit = row.get('Debit', '').strip()
                    credit = row.get('Credit', '').strip()
                    date_str = row.get('Date', '').strip()
                    
                    # Convert amount
                    if debit:
                        amount = float(debit)
                    elif credit:
                        amount = -float(credit)
                    else:
                        raise ValueError("Transaction amount missing")

                    # Convert date
                    transaction_date = datetime.strptime(date_str, '%m/%d/%Y')
                    
                    # Categorize transaction
                    category_name = categorize_transaction(description)
                    
                    # Find or create category
                    category = Category.query.filter_by(name=category_name, user_id=user_id).first()
                    if not category:
                        category = Category(name=category_name, user_id=user_id)
                        db.session.add(category)
                        db.session.commit()
                    
                    # Create Expense object
                    expense = Expense(
                        amount=amount,
                        description=description,
                        category_id=category.id,
                        date=transaction_date,
                        user_id=user_id
                    )
                    db.session.add(expense)
                    
                    # Collect training data
                    training_descriptions.append(description)
                    training_categories.append(category_name)
                    
                except Exception as e:
                    print(f"Error processing row {row}: {str(e)}")
            
            db.session.commit()  # Commit all expenses to the database
            
            # Train the categorizer with new data
            if training_descriptions and training_categories:
                train_categorizer(training_descriptions, training_categories)
                
            print("CSV import completed successfully!")
    except Exception as e:
        print(f"Error importing CSV file: {str(e)}")
        raise e


