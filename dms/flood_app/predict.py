import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
import json
from django.db.models import Q
from .models import FloodPrediction  # Assume this is available in predict.py

def generate_synthetic_data(n_samples=1000):
    # Simulate data based on flood prediction context
    np.random.seed(42)
    locations = ['Kathmandu', 'Pokhara', 'Biratnagar', 'Nepalgunj']
    probabilities = np.random.uniform(0, 1, n_samples)
    severity_levels = np.array([
        1 if p > 0.75 else 2 if p > 0.5 else 3 if p > 0.25 else 4
        for p in probabilities
    ])
    return probabilities, severity_levels

def train_predict_model():
    # Generate synthetic data (replace with real data from FloodPrediction if available)
    X, y = generate_synthetic_data()
    
    # Check if data is available
    if len(X) == 0 or len(y) == 0:
        return False

    # 80/20 train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X.reshape(-1, 1),  # Reshape for single feature
        y,
        test_size=0.2,
        random_state=42
    )

    # Train a simple Logistic Regression model
    model = LogisticRegression(multi_class='multinomial', max_iter=1000)
    model.fit(X_train, y_train)

    # Predict on test set
    y_pred = model.predict(X_test)

    # Compute confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=[1, 2, 3, 4])  # Labels: critical, high, moderate, low

    # Convert to a list of lists for JSON serialization
    cm_list = cm.tolist()

    # Print and return the confusion matrix
    print("Confusion Matrix (Rows: Actual, Columns: Predicted)")
    print("Labels: 1=Critical, 2=High, 3=Moderate, 4=Low")
    print(cm)
    return {
        'success': True,
        'confusion_matrix': cm_list
    }

# Example usage (e.g., in a view or script)
if __name__ == "__main__":
    result = train_predict_model()
    if result and result.get('success'):
        cm = result['confusion_matrix']
        print("Serialized Confusion Matrix:", json.dumps(cm))
    else:
        print("Model training failed or no data available.")