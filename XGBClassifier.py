import argparse
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier


def train(dataset_path: str):
    df = pd.read_csv(dataset_path)

    X = df.drop('label', axis=1)
    y = df['label']

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    model = XGBClassifier(
        random_state=42,
        n_estimators=350,
        max_depth=8,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        objective='multi:softprob',
        eval_metric='mlogloss'
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(f"Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred, average='weighted'):.4f}")
    print(f"Recall:    {recall_score(y_test, y_pred, average='weighted'):.4f}")
    print(f"F1 score:  {f1_score(y_test, y_pred, average='weighted'):.4f}")

    joblib.dump(model, 'xgboost_crop_model.joblib')
    joblib.dump(label_encoder, 'label_encoder.joblib')
    print('Saved: xgboost_crop_model.joblib, label_encoder.joblib')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', default='crop_recommendation.csv')
    args = parser.parse_args()
    train(args.dataset)
