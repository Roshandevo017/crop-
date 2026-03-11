import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib

df = pd.read_csv('/content/crop_recommendation.csv')
df.head()

# 1. Separate features (X) and target variable (y)
X = df.drop('label', axis=1)
y = df['label']

# 2. Initialize and fit LabelEncoder to the target variable
le = LabelEncoder()
y = le.fit_transform(y)

# 3. Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Features (X) and target (y) separated.")
print(f"X_train shape: {X_train.shape}")
print(f"X_test shape: {X_test.shape}")
print(f"y_train shape: {y_train.shape}")
print(f"y_test shape: {y_test.shape}")


# Initialize the XGBoost Classifier
xgb_model = XGBClassifier(random_state=42)

# Train the model on the training data
xgb_model.fit(X_train, y_train)

print("XGBoost model initialized and trained successfully.")

# 1. Make predictions on the test set
y_pred = xgb_model.predict(X_test)

# 2. Calculate evaluation metrics
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, average='weighted')
recall = recall_score(y_test, y_pred, average='weighted')
f1 = f1_score(y_test, y_pred, average='weighted')

# 3. Print the metrics
print(f"Model Accuracy: {accuracy:.4f}")
print(f"Model Precision (weighted): {precision:.4f}")
print(f"Model Recall (weighted): {recall:.4f}")
print(f"Model F1-Score (weighted): {f1:.4f}")

# Save the trained model to a file
joblib.dump(xgb_model, 'xgboost_crop_model_dumb.joblib')

print("XGBoost model exported successfully as 'xgboost_crop_model.joblib'")