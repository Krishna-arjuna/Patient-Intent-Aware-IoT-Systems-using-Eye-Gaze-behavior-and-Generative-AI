import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib

df = pd.read_csv("data.csv")

gaze_encoder = LabelEncoder()
df["gaze"] = gaze_encoder.fit_transform(df["gaze"])

label_encoder = LabelEncoder()
df["label"] = label_encoder.fit_transform(df["label"])

X = df[["person_id", "blink_rate", "gaze", "repeated_focus"]]
y = df["label"]

model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

joblib.dump((model, gaze_encoder, label_encoder), "model.pkl")

print("✅ Model trained")