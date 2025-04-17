import pandas as pd
import os

def search(df):
    """
    Takes user input str and searches all columns for the matching string and outputs the rows.
    """
    text = input("Enter your searchable keyword: ")
    if text=='' or text.isspace():
        print("Invalid Input")
        return None

    mask = pd.DataFrame(False, index=df.index, columns=df.columns) #create a new dataframe same size as df and initialize to false
    for col in df.columns: #loop through each column and update if string is found or not
        if df[col].dtype == object:  # Make sure the column is a string object
            mask[col] = df[col].astype(str).str.contains(text, case=False, na=False) #treat column as a str and compare the input string
    result = df[mask.any(axis=1)] #return any rows with True values

    if result.empty:
        print("No matches found.")
    
    return result

file_path = os.path.join(os.path.dirname(__file__), "Wiki_Articles.xlsx")
df = pd.read_excel(file_path)

result=search(df)
print(result)