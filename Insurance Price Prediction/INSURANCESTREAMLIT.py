# =========================================
# IMPORT LIBRARIES
# =========================================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# =========================================
# PAGE CONFIG
# =========================================
st.set_page_config(
    page_title="Insurance Cost Analysis & Prediction",
    layout="wide"
)

st.title("🏥 Insurance Cost Analysis & Prediction Dashboard")

# =========================================
# DATA LOADING
# =========================================
@st.cache_data
def load_data():
    df = pd.read_csv("E:\Labmentix Internship\Week 5\TOTAL POLICY DETAILS.csv")
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(' ', '_')
        .str.replace('.', '', regex=False)
    )
    return df

df = load_data()

# =========================================
# FEATURE ENGINEERING
# =========================================
df['bmi_category'] = pd.cut(
    df['bmi'], [0, 18.5, 25, 30, 100],
    labels=['Underweight', 'Normal', 'Overweight', 'Obese']
)

df['age_group'] = pd.cut(
    df['age'], [0, 25, 40, 55, 100],
    labels=['<25', '25–40', '40–55', '55+']
)

# =========================================
# KPI METRICS
# =========================================
st.subheader("📊 Key Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Average Policy Cost (INR)", f"{df['charges_in_inr'].mean():,.0f}")

with col2:
    st.metric("Total Policies", df.shape[0])

with col3:
    st.metric("Smoker %", f"{(df['smoker']=='yes').mean()*100:.1f}%")

# =========================================
# VISUAL ANALYTICS
# =========================================
st.subheader("📈 Visual Insights")

col1, col2 = st.columns(2)

# Gender Donut
gender_avg = df.groupby('sex')['charges_in_inr'].mean().reset_index()
fig_gender = px.pie(
    gender_avg,
    names='sex',
    values='charges_in_inr',
    hole=0.5,
    title="Average Cost Share by Gender"
)
col1.plotly_chart(fig_gender, use_container_width=True)

# Smoker Bar
smoker_avg = df.groupby('smoker')['charges_in_inr'].mean().reset_index()
fig_smoker = px.bar(
    smoker_avg,
    x='smoker',
    y='charges_in_inr',
    title="Smoker vs Non-Smoker Cost"
)
col2.plotly_chart(fig_smoker, use_container_width=True)

# Region Bar
region_avg = df.groupby('region')['charges_in_inr'].mean().reset_index()
fig_region = px.bar(
    region_avg,
    x='region',
    y='charges_in_inr',
    title="Average Cost by Region"
)
st.plotly_chart(fig_region, use_container_width=True)

# Dependents Trend
children_avg = df.groupby('children')['charges_in_inr'].mean().reset_index()
fig_children = px.line(
    children_avg,
    x='children',
    y='charges_in_inr',
    markers=True,
    title="Cost vs Number of Dependents"
)
st.plotly_chart(fig_children, use_container_width=True)

# =========================================
# MACHINE LEARNING SECTION
# =========================================
st.subheader("🤖 Insurance Cost Prediction Model")

X = df.drop(columns=['charges_in_inr', 'policy_no'])
y = df['charges_in_inr']

categorical_cols = ['sex', 'smoker', 'region', 'bmi_category', 'age_group']
numeric_cols = ['age', 'bmi', 'children']

preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(drop='first'), categorical_cols),
        ('num', 'passthrough', numeric_cols)
    ]
)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

@st.cache_resource
def train_model():
    rf_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', RandomForestRegressor(random_state=42))
    ])

    param_grid = {
        'model__n_estimators': [100, 200],
        'model__max_depth': [None, 10, 20]
    }

    grid = GridSearchCV(
        rf_pipeline,
        param_grid,
        cv=5,
        scoring='r2',
        n_jobs=-1
    )
    grid.fit(X_train, y_train)
    return grid.best_estimator_

model = train_model()
preds = model.predict(X_test)

# Model Metrics
st.markdown("### 📌 Model Performance")

st.write(pd.DataFrame({
    "Metric": ["MAE", "RMSE", "R²"],
    "Value": [
        mean_absolute_error(y_test, preds),
        np.sqrt(mean_squared_error(y_test, preds)),
        r2_score(y_test, preds)
    ]
}))

# =========================================
# USER PREDICTION
# =========================================
st.subheader("🧮 Predict Insurance Cost")

with st.form("prediction_form"):
    age = st.slider("Age", 18, 65, 30)
    bmi = st.slider("BMI", 15.0, 40.0, 25.0)
    children = st.selectbox("Children", [0, 1, 2, 3, 4])
    sex = st.selectbox("Sex", ["male", "female"])
    smoker = st.selectbox("Smoker", ["yes", "no"])
    region = st.selectbox("Region", df['region'].unique())

    submitted = st.form_submit_button("Predict")

if submitted:
    input_df = pd.DataFrame([{
        "age": age,
        "bmi": bmi,
        "children": children,
        "sex": sex,
        "smoker": smoker,
        "region": region,
        "bmi_category": pd.cut([bmi], [0,18.5,25,30,100],
                                labels=['Underweight','Normal','Overweight','Obese'])[0],
        "age_group": pd.cut([age], [0,25,40,55,100],
                            labels=['<25','25–40','40–55','55+'])[0]
    }])

    prediction = model.predict(input_df)[0]
    st.success(f"💰 Predicted Insurance Cost: INR {prediction:,.0f}")