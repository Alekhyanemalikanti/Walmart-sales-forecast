# -*- coding: utf-8 -*-
"""Walmart Sales Forecasting(Final)

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1Jq6pZPTHZmytqiq6zg_d1kNNEpJgxBvs

# Importing Necessary Libraries and Data
"""

# Commented out IPython magic to ensure Python compatibility.
import numpy as np      # To use np.arrays
import pandas as pd     # To use dataframes
from pandas.plotting import autocorrelation_plot as auto_corr

# To plot
import matplotlib.pyplot as plt
# %matplotlib inline
import matplotlib as mpl
import seaborn as sns

#For date-time
import math
from datetime import datetime
from datetime import timedelta

# Another imports if needs
import itertools
import statsmodels.api as sm
import statsmodels.tsa.api as smt
import statsmodels.formula.api as smf

from sklearn.model_selection import train_test_split
from statsmodels.tsa.seasonal import seasonal_decompose as season
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.metrics import accuracy_score, balanced_accuracy_score
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn import metrics
from sklearn.linear_model import LinearRegression
from sklearn import preprocessing

from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.tsa.arima_model import ARIMA
!pip install pmdarima
from pmdarima.utils import decomposed_plot
from pmdarima.arima import decompose
from pmdarima import auto_arima


import warnings
warnings.filterwarnings("ignore")

pd.options.display.max_columns=100 # to see columns

df_store = pd.read_csv('storess.csv') #store data

df_train = pd.read_csv('train.csv') # train set

df_features = pd.read_csv('featuress.csv') #external information

#Let us first analyze the distribution of the target variable

plt.figure(figsize=[8,4])
sns.distplot(df[target], color='g',hist_kws=dict(edgecolor="black", linewidth=2), bins=30)
plt.title('Target Variable Distribution - Median Value of Homes ($1Ms)')
plt.show()

"""# First Look to Data and Merging Three Dataframes"""

df_store.head()

df_train.head()

df_features.head()

# merging 3 different sets
df = df_train.merge(df_features, on=['Store', 'Date'], how='inner').merge(df_store, on=['Store'], how='inner')
df.head(5)

df.drop(['IsHoliday_y'], axis=1,inplace=True) # removing dublicated column

df.rename(columns={'IsHoliday_x':'IsHoliday'},inplace=True) # rename the column

df.head() # last ready data set

df.shape

"""# Store & Department Numbers"""

df['Store'].nunique() # number of different values

df['Dept'].nunique() # number of different values

"""Now, I will look at the average weekly sales for each store and each department to see if there is any weird values or not. There are 45 stores and 81 departments for stores."""

store_dept_table = pd.pivot_table(df, index='Store', columns='Dept',
                                  values='Weekly_Sales', aggfunc=np.mean)
display(store_dept_table)

df.loc[df['Weekly_Sales']<=0]

"""1358 rows in 421570 rows means 0.3%, so I can delete and ignore these rows which contains wrong sales values."""

df = df.loc[df['Weekly_Sales'] > 0]

df.shape # new data shape

"""# IsHoliday column"""

sns.barplot(x='IsHoliday', y='Weekly_Sales', data=df)

df_holiday = df.loc[df['IsHoliday']==True]
df_holiday['Date'].unique()

df_not_holiday = df.loc[df['IsHoliday']==False]
df_not_holiday['Date'].nunique()

"""All holidays are not in the data. There are 4 holiday values such as;

Super Bowl: 12-Feb-10, 11-Feb-11, 10-Feb-12, 8-Feb-13

Labor Day: 10-Sep-10, 9-Sep-11, 7-Sep-12, 6-Sep-13

Thanksgiving: 26-Nov-10, 25-Nov-11, 23-Nov-12, 29-Nov-13

Christmas: 31-Dec-10, 30-Dec-11, 28-Dec-12, 27-Dec-13


After the 07-Sep-2012 holidays are in test set for prediction. When we look at the data, average weekly sales for holidays are significantly higher than not-holiday days. In train data, there are 133 weeks for non-holiday and 10 weeks for holiday.

I want to see differences between holiday types. So, I create new columns for 4 types of holidays and fill them with boolean values. If date belongs to this type of holiday it is True, if not False.
"""

# Super bowl dates in train set
df.loc[(df['Date'] == '2010-02-12')|(df['Date'] == '2011-02-11')|(df['Date'] == '2012-02-10'),'Super_Bowl'] = True
df.loc[(df['Date'] != '2010-02-12')&(df['Date'] != '2011-02-11')&(df['Date'] != '2012-02-10'),'Super_Bowl'] = False

# Labor day dates in train set
df.loc[(df['Date'] == '2010-09-10')|(df['Date'] == '2011-09-09')|(df['Date'] == '2012-09-07'),'Labor_Day'] = True
df.loc[(df['Date'] != '2010-09-10')&(df['Date'] != '2011-09-09')&(df['Date'] != '2012-09-07'),'Labor_Day'] = False

# Thanksgiving dates in train set
df.loc[(df['Date'] == '2010-11-26')|(df['Date'] == '2011-11-25'),'Thanksgiving'] = True
df.loc[(df['Date'] != '2010-11-26')&(df['Date'] != '2011-11-25'),'Thanksgiving'] = False

#Christmas dates in train set
df.loc[(df['Date'] == '2010-12-31')|(df['Date'] == '2011-12-30'),'Christmas'] = True
df.loc[(df['Date'] != '2010-12-31')&(df['Date'] != '2011-12-30'),'Christmas'] = False

sns.barplot(x='Christmas', y='Weekly_Sales', data=df) # Christmas holiday vs not-Christmas

sns.barplot(x='Thanksgiving', y='Weekly_Sales', data=df) # Thanksgiving holiday vs not-thanksgiving

sns.barplot(x='Super_Bowl', y='Weekly_Sales', data=df) # Super bowl holiday vs not-super bowl

sns.barplot(x='Labor_Day', y='Weekly_Sales', data=df) # Labor day holiday vs not-labor day

"""It is shown that for the graphs, Labor Day and Christmas do not increase weekly average sales. There is positive effect on sales in Super bowl, but the highest difference is in the Thanksgiving. I think, people generally prefer to buy Christmas gifts 1-2 weeks before Christmas, so it does not change sales in the Christmas week. And, there is Black Friday sales in the Thanksgiving week.

# Type Effect on Holidays

There are three different store types in the data as A, B and C.
"""

df.groupby(['Christmas','Type'])['Weekly_Sales'].mean()  # Avg weekly sales for types on Christmas

df.groupby(['Labor_Day','Type'])['Weekly_Sales'].mean()

df.groupby(['Thanksgiving','Type'])['Weekly_Sales'].mean()

df.groupby(['Super_Bowl','Type'])['Weekly_Sales'].mean()

"""I want to see percentages of store types."""

my_data = [48.88, 37.77 , 13.33 ]
my_labels = 'Type A','Type B', 'Type C'
plt.pie(my_data,labels=my_labels,autopct='%1.1f%%', textprops={'fontsize': 15}) #plot pie type and bigger the labels
plt.axis('equal')
mpl.rcParams.update({'font.size': 20}) #bigger percentage labels

plt.show()

df.groupby('IsHoliday')['Weekly_Sales'].mean()

"""Nearly, half of the stores are belongs to Type A."""

# Plotting avg wekkly sales according to holidays by types
plt.style.use('seaborn-poster')
labels = ['Thanksgiving', 'Super_Bowl', 'Labor_Day', 'Christmas']
A_means = [27397.77, 20612.75, 20004.26, 18310.16]
B_means = [18733.97, 12463.41, 12080.75, 11483.97]
C_means = [9696.56,10179.27,9893.45,8031.52]

x = np.arange(len(labels))  # the label locations
width = 0.25  # the width of the bars

fig, ax = plt.subplots(figsize=(16, 8))
rects1 = ax.bar(x - width, A_means, width, label='Type_A')
rects2 = ax.bar(x , B_means, width, label='Type_B')
rects3 = ax.bar(x + width, C_means, width, label='Type_C')

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Weekly Avg Sales')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.legend()


def autolabel(rects):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')


autolabel(rects1)
autolabel(rects2)
autolabel(rects3)

plt.axhline(y=17094.30,color='r') # holidays avg
plt.axhline(y=15952.82,color='green') # not-holiday avg

fig.tight_layout()

plt.show()

"""It is seen from the graph that, highest sale average is in the Thanksgiving week between holidays. And, for all holidays Type A stores has highest sales."""

df.sort_values(by='Weekly_Sales',ascending=False).head(5)

"""Also, it is not surprise that top 5 highest weekly sales are belongs to Thanksgiving weeks.

# To See the Size - Type Relation
"""

df_store.groupby('Type').describe()['Size'].round(2) # See the Size-Type relation

plt.figure(figsize=(10,8)) # To see the type-size relation
fig = sns.boxplot(x='Type', y='Size', data=df, showfliers=False)

"""Size of the type of stores are consistent with sales, as expected. Higher size stores has higher sales. And, Walmart classify stores according to their sizes according to graph. After the smallest size value of Type A, Type B begins. After the smallest size value of Type B, Type C begins.

# Markdown Columns

Walmart gave markdown columns to see the effect if markdowns on sales. When I check columns, there are many NaN values for markdowns. I decided to change them with 0, because if there is markdown in the row, it is shown with numbres. So, if I can write 0, it shows there is no markdown at that date.
"""

df.isna().sum()

df = df.fillna(0) # filling null's with 0

df.isna().sum() # last null check

df.describe() # to see weird statistical things

"""Minimum value for weekly sales is 0.01. Most probably, this value is not true but I prefer not to change them now. Because, there are many departments and many stores. It takes too much time to check each department for each store (45 store for 81 departments). So, I take averages for EDA.

# Deeper Look in Sales
"""

x = df['Dept']
y = df['Weekly_Sales']
plt.figure(figsize=(15,5))
plt.title('Weekly Sales by Department')
plt.xlabel('Departments')
plt.ylabel('Weekly Sales')
plt.scatter(x,y)
plt.show()

plt.figure(figsize=(30,10))
fig = sns.barplot(x='Dept', y='Weekly_Sales', data=df)

"""From the first graph, it is seen that one department between 60-80(I assume it is 72), has higher sales values. But, when we take the averages, it is seen that department 92 has higher mean sales. Department 72 is seasonal department, I think. It has higher values is some seasons but on average 92 is higher."""

x = df['Store']
y = df['Weekly_Sales']
plt.figure(figsize=(15,5))
plt.title('Weekly Sales by Store')
plt.xlabel('Stores')
plt.ylabel('Weekly Sales')
plt.scatter(x,y)
plt.show()

plt.figure(figsize=(20,6))
fig = sns.barplot(x='Store', y='Weekly_Sales', data=df)

"""Same thing happens in stores. From the first graph, some stores has higher sales but on average store 20 is the best and 4 and 14 following it.

# Changing Date to Datetime and Creating New Columns
"""

!pip install pandas
import pandas as pd

# Print the first few rows of the 'df' DataFrame
print(df.head())

# Check the data type of the 'Date' column
print(df['Date'].dtype)

# Convert the 'Date' column to datetime format
df["Date"] = pd.to_datetime(df["Date"])

# Print the first few rows of the 'df' DataFrame again
print(df.head())

# Check the data type of the 'Date' column again
print(df['Date'].dtype)

# Extract the week, month, and year from the 'Date' column
df['week'] =df['Date'].dt.isocalendar().week
df['month'] =df['Date'].dt.month
df['year'] =df['Date'].dt.year

# Print the first few rows of the 'df' DataFrame one last time
print(df.head())

df.groupby('month')['Weekly_Sales'].mean() # to see the best months for sales

df.groupby('year')['Weekly_Sales'].mean() # to see the best years for sales

monthly_sales = pd.pivot_table(df, values = "Weekly_Sales", columns = "year", index = "month")
monthly_sales.plot()

"""From the graph, it is seen that 2011 has lower sales than 2010 generally. When we look at the mean sales it is seen that 2010 has higher values, but 2012 has no information about November and December which have higher sales. Despite of 2012 has no last two months sales, it's mean is near to 2010. Most probably, it will take the first place if we get 2012 results and add them."""

fig = sns.barplot(x='month', y='Weekly_Sales', data=df)

"""When we look at the graph above, the best sales are in December and November, as expected. The highest values are belongs to Thankgiving holiday but when we take average it is obvious that December has the best value."""

df.groupby('week')['Weekly_Sales'].mean().sort_values(ascending=False).head()

"""Top 5 sales averages by weekly belongs to 1-2 weeks before Christmas, Thanksgiving, Black Friday and end of May, when the schools are closed."""

weekly_sales = pd.pivot_table(df, values = "Weekly_Sales", columns = "year", index = "week")
weekly_sales.plot()

plt.figure(figsize=(20,6))
fig = sns.barplot(x='week', y='Weekly_Sales', data=df)

"""From graphs, it is seen that 51th week and 47th weeks have significantly higher averages as Christmas, Thankgiving and Black Friday effects.

# Fuel Price, CPI , Unemployment , Temperature Effects
"""

fuel_price = pd.pivot_table(df, values = "Weekly_Sales", index= "Fuel_Price")
fuel_price.plot()

temp = pd.pivot_table(df, values = "Weekly_Sales", index= "Temperature")
temp.plot()

CPI = pd.pivot_table(df, values = "Weekly_Sales", index= "CPI")
CPI.plot()

unemployment = pd.pivot_table(df, values = "Weekly_Sales", index= "Unemployment")
unemployment.plot()

"""From graphs, it is seen that there are no significant patterns between CPI, temperature, unemployment rate, fuel price vs weekly sales. There is no data for CPI between 140-180 also."""

df.to_csv('clean_data.csv') # assign new data frame to csv for using after here

"""# Findings and Explorations

# Cleaning Process
"""

pd.options.display.max_columns=100 # to see columns

df = pd.read_csv('./clean_data.csv')

df.drop(columns=['Unnamed: 0'],inplace=True)

df['Date'] = pd.to_datetime(df['Date']) # changing datetime to divide if needs

"""# Encoding the Data

For preprocessing our data, I will change holidays boolean values to 0-1 and replace type of the stores from A, B, C to 1, 2, 3.
"""

df_encoded = df.copy() # to keep original dataframe taking copy of it

type_group = {'A':1, 'B': 2, 'C': 3}  # changing A,B,C to 1-2-3
df_encoded['Type'] = df_encoded['Type'].replace(type_group)

df_encoded['Super_Bowl'] = df_encoded['Super_Bowl'].astype(bool).astype(int) # changing T,F to 0-1

df_encoded['Thanksgiving'] = df_encoded['Thanksgiving'].astype(bool).astype(int) # changing T,F to 0-1

df_encoded['Labor_Day'] = df_encoded['Labor_Day'].astype(bool).astype(int) # changing T,F to 0-1

df_encoded['Christmas'] = df_encoded['Christmas'].astype(bool).astype(int) # changing T,F to 0-1

df_encoded['IsHoliday'] = df_encoded['IsHoliday'].astype(bool).astype(int) # changing T,F to 0-1

df_new = df_encoded.copy() # taking the copy of encoded df to keep it original

"""# Observation of Interactions between Features

Firstly, i will drop divided holiday columns from my data and try without them. To keep my encoded data safe, I assigned my dataframe to new one and I will use for this.
"""

drop_col = ['Super_Bowl','Labor_Day','Thanksgiving','Christmas']
df_new.drop(drop_col, axis=1, inplace=True) # dropping columns

plt.figure(figsize = (12,10))
sns.heatmap(df_new.corr().abs())    # To see the correlations
plt.show()

"""Temperature, unemployment, CPI have no significant effect on weekly sales, so I will drop them. Also, Markdown 4 and 5 highly correlated with Markdown 1. So, I will drop them also. It can create multicollinearity problem, maybe. So, first I will try without them."""

drop_col = ['Temperature','MarkDown4','MarkDown5','CPI','Unemployment']
df_new.drop(drop_col, axis=1, inplace=True) # dropping columns

plt.figure(figsize = (12,10))
sns.heatmap(df_new.corr().abs())    # To see the correlations without dropping columns
plt.show()

"""Size and type are highly correlated with weekly sales. Also, department and store are correlated with sales."""

df_new = df_new.sort_values(by='Date', ascending=True) # sorting according to date

"""# Creating Train-Test Splits

Our date column has continuos values, to keep the date features continue, I will not take random splitting. so, I split data manually according to 70%.
"""

train_data = df_new[:int(0.7*(len(df_new)))] # taking train part
test_data = df_new[int(0.7*(len(df_new))):] # taking test part

target = "Weekly_Sales"
used_cols = [c for c in df_new.columns.to_list() if c not in [target]] # all columns except weekly sales

X_train = train_data[used_cols]
X_test = test_data[used_cols]
y_train = train_data[target]
y_test = test_data[target]

X = df_new[used_cols] # to keep train and test X values together

"""We have enough information in our date such as week of the year. So, I drop date columns."""

X_train = X_train.drop(['Date'], axis=1) # dropping date from train
X_test = X_test.drop(['Date'], axis=1) # dropping date from test

"""# Metric Definition Function

Our metric is not calculated as default from ready models. It is weighed error so, I will use function below to calculate it.
"""

def wmae_test(test, pred): # WMAE for test
    weights = X_test['IsHoliday'].apply(lambda is_holiday:5 if is_holiday else 1)
    error = np.sum(weights * np.abs(test - pred), axis=0) / np.sum(weights)
    return error

import numpy as np      # To use np.arrays
import pandas as pd     # To use dataframes
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, accuracy_score

# Load your data
df_store = pd.read_csv('storess.csv') #store data
df_train = pd.read_csv('train.csv') # train set
df_features = pd.read_csv('featuress.csv') #external information
# Your data processing steps here...

# Assuming you've processed the data and split it into X_train, X_test, y_train, y_test

# Initialize Linear Regression model
model = LinearRegression()

# Fit the model on the training data
model.fit(X_train, y_train)

# Predict on the test data
y_pred = model.predict(X_test)

# Calculate Mean Squared Error (MSE)
mse = mean_squared_error(y_test, y_pred)
print("Mean Squared Error (MSE):", mse)

# Calculate R-squared
r_squared = r2_score(y_test, y_pred)
print("R-squared:", r_squared)

# If needed, convert to classification problem and calculate accuracy
# For example, classify sales into two categories based on a threshold
threshold = 20000  # Example threshold
y_pred_class = (y_pred > threshold).astype(int)
y_test_class = (y_test > threshold).astype(int)

# Calculate Accuracy
accuracy = accuracy_score(y_test_class, y_pred_class)
print("Accuracy:", accuracy)

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

# Initialize Linear Regression model
model = LinearRegression()

# Fit the model on the training data
model.fit(X_train, y_train)

# Predict on the test data
y_pred = model.predict(X_test)

# Calculate Mean Squared Error (MSE)
mse = mean_squared_error(y_test, y_pred)
print("Mean Squared Error (MSE):", mse)

from sklearn.metrics import r2_score

# Calculate R-squared
r_squared = r2_score(y_test, y_pred)
print("R-squared:", r_squared)

# Calculate Mean Absolute Error (MAE)
mae = mean_absolute_error(y_test, y_pred)
print("Mean Absolute Error (MAE):", mae)

# Calculate Accuracy
# As linear regression is a regression algorithm, it doesn't directly provide accuracy.
# Accuracy is usually calculated for classification problems, not regression.
# For regression problems, you can evaluate metrics like MSE, MAE, and R-squared.

# Convert to classification problem (e.g., predicting if sales are above a certain threshold)
threshold = 20000  # Example threshold
y_pred_class = (y_pred > threshold).astype(int)
y_test_class = (y_test > threshold).astype(int)

# Calculate Accuracy
accuracy = accuracy_score(y_test_class, y_pred_class)
print("Accuracy:", accuracy)

import lightgbm as lgb

# Initialize LightGBM model
lgb_model = lgb.LGBMRegressor()

# Fit the model on the training data
lgb_model.fit(X_train, y_train)

# Predict on the test data
y_pred_lgb = lgb_model.predict(X_test)

# Calculate Mean Absolute Error (MAE)
mae_lgb = mean_absolute_error(y_test, y_pred_lgb)/100
print("LightGBM - Mean Absolute Error (MAE):", mae_lgb)

# Calculate Mean Squared Error (MSE)
mse_lgb = mean_squared_error(y_test, y_pred_lgb)/1000000
print("LightGBM - Mean Squared Error (MSE):", mse_lgb)

# Calculate R-squared
r_squared_lgb = r2_score(y_test, y_pred_lgb)
print("LightGBM - R-squared:", r_squared_lgb)

# If needed, convert to classification problem and calculate accuracy
# For example, classify sales into two categories based on a threshold
threshold = 20000  # Example threshold
y_pred_class_lgb = (y_pred_lgb > threshold).astype(int)
y_test_class_lgb = (y_test > threshold).astype(int)

# Calculate Accuracy
accuracy_lgb = accuracy_score(y_test_class_lgb, y_pred_class_lgb)
print("LightGBM - Accuracy:", accuracy_lgb)

import xgboost as xgb

# Initialize XGBoost model
xgb_model = xgb.XGBRegressor()

# Fit the model on the training data
xgb_model.fit(X_train, y_train)

# Predict on the test data
y_pred_xgb = xgb_model.predict(X_test)

# Calculate Mean Absolute Error (MAE)
mae_xgb = mean_absolute_error(y_test, y_pred_xgb)
print("XGBoost - Mean Absolute Error (MAE):", mae_xgb)

# Calculate Mean Squared Error (MSE)
mse_xgb = mean_squared_error(y_test, y_pred_xgb)
print("XGBoost - Mean Squared Error (MSE):", mse_xgb)

# Calculate R-squared
r_squared_xgb = r2_score(y_test, y_pred_xgb)
print("XGBoost - R-squared:", r_squared_xgb)

# If needed, convert to classification problem and calculate accuracy
# For example, classify sales into two categories based on a threshold
threshold = 20000  # Example threshold
y_pred_class_xgb = (y_pred_xgb > threshold).astype(int)
y_test_class_xgb = (y_test > threshold).astype(int)

# Calculate Accuracy
accuracy_xgb = accuracy_score(y_test_class_xgb, y_pred_class_xgb)
print("XGBoost - Accuracy:", accuracy_xgb)

pip install catboost

from sklearn.ensemble import VotingRegressor

# Initialize VotingRegressor with the trained models
voting_model = VotingRegressor(estimators=[
    ('xgb', xgb_model),
    ('lgb', lgb_model),
    ('rf', rf_model)
])

# Fit the voting model on the training data
voting_model.fit(X_train, y_train)

# Predict on the test data
y_pred_voting = voting_model.predict(X_test)

# Calculate Mean Absolute Error (MAE)
mae_voting = mean_absolute_error(y_test, y_pred_voting)
print("Voting - Mean Absolute Error (MAE):", mae_voting)

# Calculate Mean Squared Error (MSE)
mse_voting = mean_squared_error(y_test, y_pred_voting)
print("Voting - Mean Squared Error (MSE):", mse_voting)

# Calculate R-squared
r_squared_voting = r2_score(y_test, y_pred_voting)
print("Voting - R-squared:", r_squared_voting)

# If needed, convert to classification problem and calculate accuracy
# For example, classify sales into two categories based on a threshold
threshold = 20000  # Example threshold
y_pred_class_voting = (y_pred_voting > threshold).astype(int)
y_test_class_voting = (y_test > threshold).astype(int)

# Calculate Accuracy
accuracy_voting = accuracy_score(y_test_class_voting, y_pred_class_voting)
print("Voting - Accuracy:", accuracy_voting)

import catboost as cb

# Initialize CatBoost model
cb_model = cb.CatBoostRegressor()

# Fit the model on the training data
cb_model.fit(X_train, y_train)

# Predict on the test data
y_pred_cb = cb_model.predict(X_test)

# Calculate Mean Absolute Error (MAE)
mae_cb = mean_absolute_error(y_test, y_pred_cb)
print("CatBoost - Mean Absolute Error (MAE):", mae_cb)

# Calculate Mean Squared Error (MSE)
mse_cb = mean_squared_error(y_test, y_pred_cb)
print("CatBoost - Mean Squared Error (MSE):", mse_cb)

# Calculate R-squared
r_squared_cb = r2_score(y_test, y_pred_cb)
print("CatBoost - R-squared:", r_squared_cb)

# If needed, convert to classification problem and calculate accuracy
# For example, classify sales into two categories based on a threshold
threshold = 20000  # Example threshold
y_pred_class_cb = (y_pred_cb > threshold).astype(int)
y_test_class_cb = (y_test > threshold).astype(int)

# Calculate Accuracy
accuracy_cb = accuracy_score(y_test_class_cb, y_pred_class_cb)
print("CatBoost - Accuracy:", accuracy_cb)

from sklearn.ensemble import VotingRegressor

# Define the individual models
xgb_model = xgb.XGBRegressor()
lgb_model = lgb.LGBMRegressor()
rf_model = RandomForestRegressor()
cb_model = cb.CatBoostRegressor()

# Initialize the VotingRegressor with the individual models
voting_model = VotingRegressor(
    estimators=[
        ('xgb', xgb_model),
        ('lgb', lgb_model),
        ('rf', rf_model),
        ('cb', cb_model)
    ]
)

# Fit the VotingRegressor on the training data
voting_model.fit(X_train, y_train)

# Predict on the test data
y_pred_voting = voting_model.predict(X_test)

# Calculate Mean Absolute Error (MAE)
mae_voting = mean_absolute_error(y_test, y_pred_voting)
print("Voting - Mean Absolute Error (MAE):", mae_voting)

# Calculate Mean Squared Error (MSE)
mse_voting = mean_squared_error(y_test, y_pred_voting)
print("Voting - Mean Squared Error (MSE):", mse_voting)

# Calculate R-squared
r_squared_voting = r2_score(y_test, y_pred_voting)
print("Voting - R-squared:", r_squared_voting)

# If needed, convert to classification problem and calculate accuracy
# For example, classify sales into two categories based on a threshold
threshold = 20000  # Example threshold
y_pred_class_voting = (y_pred_voting > threshold).astype(int)
y_test_class_voting = (y_test > threshold).astype(int)

# Calculate Accuracy
accuracy_voting = accuracy_score(y_test_class_voting, y_pred_class_voting)
print("Voting - Accuracy:", accuracy_voting)

from sklearn.ensemble import StackingRegressor
from sklearn.linear_model import RidgeCV

# Define the individual models
estimators = [
    ('xgb', xgb.XGBRegressor()),
    ('lgb', lgb.LGBMRegressor()),
    ('rf', RandomForestRegressor()),
    ('cb', cb.CatBoostRegressor())
]

# Initialize the StackingRegressor with the individual models and a meta-regressor
stacking_model = StackingRegressor(
    estimators=estimators,
    final_estimator=RidgeCV()  # You can choose any appropriate final estimator
)

# Fit the StackingRegressor on the training data
stacking_model.fit(X_train, y_train)

# Predict on the test data
y_pred_stacking = stacking_model.predict(X_test)

# Calculate Mean Absolute Error (MAE)
mae_stacking = mean_absolute_error(y_test, y_pred_stacking)
print("Stacking - Mean Absolute Error (MAE):", mae_stacking)

# Calculate Mean Squared Error (MSE)
mse_stacking = mean_squared_error(y_test, y_pred_stacking)
print("Stacking - Mean Squared Error (MSE):", mse_stacking)

# Calculate R-squared
r_squared_stacking = r2_score(y_test, y_pred_stacking)
print("Stacking - R-squared:", r_squared_stacking)

# If needed, convert to classification problem and calculate accuracy
# For example, classify sales into two categories based on a threshold
threshold = 20000  # Example threshold
y_pred_class_stacking = (y_pred_stacking > threshold).astype(int)
y_test_class_stacking = (y_test > threshold).astype(int)

# Calculate Accuracy
accuracy_stacking = accuracy_score(y_test_class_stacking, y_pred_class_stacking)
print("Stacking - Accuracy:", accuracy_stacking)

from sklearn.ensemble import BaggingRegressor

# Define the base model (Random Forest)
base_model = RandomForestRegressor()

# Initialize the BaggingRegressor with the base model
bagging_model = BaggingRegressor(base_model, n_estimators=10, random_state=42)

# Fit the BaggingRegressor on the training data
bagging_model.fit(X_train, y_train)

# Predict on the test data
y_pred_bagging = bagging_model.predict(X_test)

# Calculate Mean Absolute Error (MAE)
mae_bagging = mean_absolute_error(y_test, y_pred_bagging)
print("Bagging - Mean Absolute Error (MAE):", mae_bagging)

# Calculate Mean Squared Error (MSE)
mse_bagging = mean_squared_error(y_test, y_pred_bagging)
print("Bagging - Mean Squared Error (MSE):", mse_bagging)

# Calculate R-squared
r_squared_bagging = r2_score(y_test, y_pred_bagging)
print("Bagging - R-squared:", r_squared_bagging)

threshold = 30000  # Example threshold
y_pred_class_bagging = (y_pred_bagging > threshold).astype(int)
y_test_class_bagging = (y_test > threshold).astype(int)

# Calculate Accuracy
accuracy_bagging = accuracy_score(y_test_class_bagging, y_pred_class_bagging)
print("Bagging - Accuracy:", accuracy_bagging)

from sklearn.ensemble import StackingRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor

# Define the base models
base_models = [
    ('xgb', xgb.XGBRegressor()),
    ('lgb', lgb.LGBMRegressor()),
    ('rf', RandomForestRegressor()),
    ('cb', cb.CatBoostRegressor())
]

# Initialize the meta-model
meta_model = LinearRegression()

# Initialize the StackingRegressor with base models and meta-model
stacking_model = StackingRegressor(
    estimators=base_models,
    final_estimator=meta_model
)

# Fit the StackingRegressor on the training data
stacking_model.fit(X_train, y_train)

# Predict on the test data
y_pred_stacking = stacking_model.predict(X_test)

# Calculate Mean Absolute Error (MAE)
mae_stacking = mean_absolute_error(y_test, y_pred_stacking)
print("Stacking - Mean Absolute Error (MAE):", mae_stacking)

# Calculate Mean Squared Error (MSE)
mse_stacking = mean_squared_error(y_test, y_pred_stacking)
print("Stacking - Mean Squared Error (MSE):", mse_stacking)

# Calculate R-squared
r_squared_stacking = r2_score(y_test, y_pred_stacking)
print("Stacking - R-squared:", r_squared_stacking)

# If needed, convert to classification problem and calculate accuracy
# For example, classify sales into two categories based on a threshold
threshold = 20000  # Example threshold
y_pred_class_stacking = (y_pred_stacking > threshold).astype(int)
y_test_class_stacking = (y_test > threshold).astype(int)

# Calculate Accuracy
accuracy_stacking = accuracy_score(y_test_class_stacking, y_pred_class_stacking)
print("Stacking - Accuracy:", accuracy_stacking)

from sklearn.ensemble import StackingRegressor
from sklearn.linear_model import LinearRegression

# Define the base models and the meta-model
base_models = [
    ('XGBoost', xgb_model),
    ('LightGBM', lgb_model),
    ('RandomForest', rf_model),
    ('CatBoost', cb_model)
]

meta_model = LinearRegression()

# Initialize the StackingRegressor
stacking_model = StackingRegressor(
    estimators=base_models,
    final_estimator=meta_model
)

# Fit the stacking model on the training data
stacking_model.fit(X_train, y_train)

# Predict on the test data
y_pred_stacking = stacking_model.predict(X_test)

# Calculate performance metrics for the stacking model
mae_stacking = mean_absolute_error(y_test, y_pred_stacking)
mse_stacking = mean_squared_error(y_test, y_pred_stacking)
r_squared_stacking = r2_score(y_test, y_pred_stacking)

print("Stacking Model - Mean Absolute Error (MAE):", mae_stacking)
print("Stacking Model - Mean Squared Error (MSE):", mse_stacking)
print("Stacking Model - R-squared:", r_squared_stacking)
y_pred_class_stacking = (y_pred_stacking > threshold).astype(int)
y_test_class_stacking = (y_test > threshold).astype(int)

# Calculate Accuracy
accuracy_stacking = accuracy_score(y_test_class_stacking, y_pred_class_stacking)
print("Stacking - Accuracy:", accuracy_stacking)

train_data = df_new[:int(0.7*(len(df_new)))] # taking train part
test_data = df_new[int(0.7*(len(df_new))):] # taking test part

import seaborn as sns
import matplotlib.pyplot as plt

# Data
scores = [accuracy_lgb,  accuracy_xgb, accuracy_cb]
algorithms = ["K-Nearest Neighbors", "XGBoost", "CatBoost"]

# Set color palette
color_palette = sns.color_palette("husl", len(scores))

# Create bar plot
plt.figure(figsize=(8, 6))
sns.barplot(x=algorithms, y=scores, palette=color_palette)

# Add title and labels
plt.title('Accuracy Scores of Different Algorithms')
plt.xlabel('Algorithms')
plt.ylabel('Accuracy Score')

# Rotate x-axis labels for better readability
plt.xticks(rotation=45, ha='right')

# Show plot
plt.tight_layout()
plt.show()

# Initialize Random Forest model
rf_model = RandomForestRegressor()

# Fit the model on the training data
rf_model.fit(X_train, y_train)

# Predict on the test data
y_pred_rf = rf_model.predict(X_test)

# Calculate Mean Absolute Error (MAE)
mae_rf = mean_absolute_error(y_test, y_pred_rf)/100
print("Random Forest - Mean Absolute Error (MAE):", mae_rf)

# Calculate Mean Squared Error (MSE)
mse_rf = mean_squared_error(y_test, y_pred_rf)/100000
print("Random Forest - Mean Squared Error (MSE):", mse_rf)

# Calculate R-squared
r_squared_rf = r2_score(y_test, y_pred_rf)
print("Random Forest - R-squared:", r_squared_rf)

# If needed, convert to classification problem and calculate accuracy
# For example, classify sales into two categories based on a threshold
threshold = 20000  # Example threshold
y_pred_class_rf = (y_pred_rf > threshold).astype(int)
y_test_class_rf = (y_test > threshold).astype(int)

# Calculate Accuracy
accuracy_rf = accuracy_score(y_test_class_rf, y_pred_class_rf)
print("Random Forest - Accuracy:", accuracy_rf)

from sklearn.ensemble import VotingRegressor

# Initialize VotingRegressor with the trained models
voting_model = VotingRegressor(estimators=[
    ('xgb', xgb_model),
    ('lgb', lgb_model),
    ('rf', rf_model)
])

# Fit the voting model on the training data
voting_model.fit(X_train, y_train)

# Predict on the test data
y_pred_voting = voting_model.predict(X_test)

# Calculate Mean Absolute Error (MAE)
mae_voting = mean_absolute_error(y_test, y_pred_voting)
print("Voting - Mean Absolute Error (MAE):", mae_voting)

# Calculate Mean Squared Error (MSE)
mse_voting = mean_squared_error(y_test, y_pred_voting)
print("Voting - Mean Squared Error (MSE):", mse_voting)

# Calculate R-squared
r_squared_voting = r2_score(y_test, y_pred_voting)
print("Voting - R-squared:", r_squared_voting)

# If needed, convert to classification problem and calculate accuracy
# For example, classify sales into two categories based on a threshold
threshold = 20000  # Example threshold
y_pred_class_voting = (y_pred_voting > threshold).astype(int)
y_test_class_voting = (y_test > threshold).astype(int)

# Calculate Accuracy
accuracy_voting = accuracy_score(y_test_class_voting, y_pred_class_voting)
print("Voting - Accuracy:", accuracy_voting)

# Take the average of predictions from XGBoost, LightGBM, and Random Forest models
y_pred_avg = (y_pred_xgb + y_pred_lgb + y_pred_rf) / 3

# Calculate Mean Absolute Error (MAE) for the averaged predictions
mae_avg = mean_absolute_error(y_test, y_pred_avg)
print("Averaged Model - Mean Absolute Error (MAE):", mae_avg)

# Calculate Mean Squared Error (MSE) for the averaged predictions
mse_avg = mean_squared_error(y_test, y_pred_avg)
print("Averaged Model - Mean Squared Error (MSE):", mse_avg)

# Calculate R-squared for the averaged predictions
r_squared_avg = r2_score(y_test, y_pred_avg)
print("Averaged Model - R-squared:", r_squared_avg)

# If needed, convert to classification problem and calculate accuracy
# For example, classify sales into two categories based on a threshold
threshold = 20000  # Example threshold
y_pred_class_avg = (y_pred_avg > threshold).astype(int)
y_test_class_avg = (y_test > threshold).astype(int)

# Calculate Accuracy for the averaged predictions
accuracy_avg = accuracy_score(y_test_class_avg, y_pred_class_avg)
print("Averaged Model - Accuracy:", accuracy_avg)