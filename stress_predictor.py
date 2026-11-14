import joblib
import pandas as pd

# Load the trained model and preprocessing pipeline.
model = joblib.load("student_stress_model.pkl")


def predict_stress(student_data):
    # Convert student information into a DataFrame.
    student_df = pd.DataFrame([student_data])

    # Predict the dataset-defined stress category.
    prediction = model.predict(student_df)

    return prediction[0]
