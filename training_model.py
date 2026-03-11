import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder,StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import joblib


df = pd.read_csv(r"C:\Users\Roshan\Videos\data train\dataset.csv")
print(df.head())
print(df.info())
print(df.isnull().sum())
df = df.dropna()
X = df[['N','P','K','temperature','humidity','pH','rainfall']]
Y = df["crop"] 
print(X.head())
print(Y.head())
label_encoder = LabelEncoder()
Y_encoded = label_encoder.fit_transform(Y)
joblib.dump(label_encoder, "label.pkl")
print("Model saved successfully!")

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
joblib.dump(scaler, "scaler.pkl")
print("Model saved successfully!")

X_train, X_test, Y_train, Y_test = train_test_split(
    X,Y,test_size=0.2,
    random_state=42
)
print("Training size:", X_train.shape)
print("Testing size:", X_test.shape)
model = RandomForestClassifier()
model.fit(X_train,Y_train)
Y_pred = model.predict(X_test)
accuracy = accuracy_score(Y_test, Y_pred)
print("Model Accuracy:", accuracy * 100, "%")
joblib.dump(model, "model.pkl")
print("Model saved successfully!")











