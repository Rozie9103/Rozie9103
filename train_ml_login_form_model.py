import joblib
from bs4 import BeautifulSoup
import numpy as np
from sklearn.linear_model import LogisticRegression

# Import dataset dan fungsi ekstraksi fitur
from ml_login_form_dataset import dataset

def extract_form_features(form):
    features = {}
    inputs = form.find_all('input')
    features['input_count'] = len(inputs)
    features['password_count'] = sum(1 for i in inputs if i.get('type') == 'password')
    features['text_count'] = sum(1 for i in inputs if i.get('type') == 'text')
    features['email_count'] = sum(1 for i in inputs if i.get('type') == 'email')
    features['submit_count'] = sum(1 for i in inputs if i.get('type') == 'submit')
    # Kata kunci pada label/placeholder
    keywords = ['login', 'user', 'username', 'email', 'pass', 'signin']
    label_text = ' '.join([l.get_text().lower() for l in form.find_all('label')])
    placeholder_text = ' '.join([i.get('placeholder', '').lower() for i in inputs])
    features['keyword_in_label'] = int(any(k in label_text for k in keywords))
    features['keyword_in_placeholder'] = int(any(k in placeholder_text for k in keywords))
    return [
        features['input_count'],
        features['password_count'],
        features['text_count'],
        features['email_count'],
        features['submit_count'],
        features['keyword_in_label'],
        features['keyword_in_placeholder'],
    ]

# Proses dataset
X = []
y = []
for html, label in dataset:
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find('form')
    if form:
        X.append(extract_form_features(form))
        y.append(label)

X = np.array(X)
y = np.array(y)

# Training model
model = LogisticRegression()
model.fit(X, y)
joblib.dump(model, 'ml_login_form_model.pkl')
print("Model trained and saved as ml_login_form_model.pkl")