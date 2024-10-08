import pandas as pd
import streamlit as st
from openai import OpenAI
import requests
import pandas as pd 
import ast

def clean_text_data(df):
    # Your text data cleaning logic here (similar to what we've done previously)
    cleaned_text_data = []
    current_question = None
    
    for row in df[0]:  # Assuming all data is in the first column
        if isinstance(row, str) and "Description: Q" in row:
            # Extract the question
            current_question = row
        elif current_question and isinstance(row, str) and row.strip():
            # Append the current question and response
            cleaned_text_data.append([current_question, row])
    
    # Create DataFrame and consolidate answers for each question
    consolidated_text_df = pd.DataFrame(cleaned_text_data, columns=['Question', 'Answer'])
    consolidated_text_df = consolidated_text_df.groupby('Question')['Answer'].apply(lambda x: ' | '.join(x)).reset_index()
    
    return consolidated_text_df[0:23]

def clean_numerical_data(df):
    # Load the data and filter based on previous logic
    df_numerical = df.iloc[:, :3]  # Get the first three columns

    # Remove rows where the second column is NaN or empty
    df_numerical = df_numerical[df_numerical[1].notna() & (df_numerical[1] != '')]

    # Find the index of the first occurrence of 'Percentage' in the second column
    percentage_index = df_numerical[df_numerical[1] == 'Percentage'].index

    # If 'Percentage' is found, slice the DataFrame to keep only the rows above it
    if not percentage_index.empty:
        filtered_numerical_df = df_numerical.iloc[:percentage_index[0]]
    else:
        filtered_numerical_df = df_numerical  # If not found, keep all

    # Reset index for a clean DataFrame
    filtered_numerical_df.reset_index(drop=True, inplace=True)

    return filtered_numerical_df

key = st.secrets['openai']['KEY']

def get_openai_response(api_key,messages):
   client = OpenAI(api_key=api_key)
   response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      temperature=1,
      messages=messages
   )
   return response.choices[0].message.content

# Streamlit app
st.sidebar.title("MSS Survey Analysis Tool")
st.sidebar.write("Navigation")
page = st.sidebar.radio("Select a page", ["Data Cleaning", "Survey Text Analysis"])

if page == "Data Cleaning":
    st.title("MSS Survey Data Cleaner")
    st.write("Created For MS Solutions PL Survey")

    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

    if uploaded_file is not None:
        # Read the uploaded Excel file
        df = pd.read_excel(uploaded_file, header=None)

        # Process text responses
        text_data = clean_text_data(df)
        st.write("Text Responses:")
        st.dataframe(text_data)

        # Process numerical responses
        numerical_data = clean_numerical_data(df)
        st.write("Numerical Responses:")
        st.dataframe(numerical_data)

        # Download buttons for the cleaned data
        text_csv = text_data.to_csv(index=False).encode('utf-8')
        numerical_csv = numerical_data.to_csv(index=False).encode('utf-8')

        st.download_button("Download Text Responses", text_csv, "text_responses.csv", "text/csv")
        st.download_button("Download Numerical Responses", numerical_csv, "numerical_responses.csv", "text/csv")

elif page == "Survey Text Analysis":

    st.title('Survey Analysis Tool')

    st.write("Paste the survey question below:")
    survey_question = st.text_input("", key = "Q")
    if survey_question:

        st.write("Paste the responses to that survey question below, include ALL responses in one line:")
        survey_responses = st.text_input("", key = "R")
        if survey_responses:

            st.write("Click the button to generate insights from the survey responses:")
            if st.button("Generate"):
                full_message = "Qustion: " + survey_question + " Responses: " + survey_responses
                messages = [
                {"role": "system", "content": 'Hello! You are a survey analysis tool, you will be given a question from a survey and some responses, your job is to analyze the responses and provide the top 3 insights from the responses. For each insight please also list the number of times that insight appeared among all responses. For example if the question was about customer satisfaction and the term "confused" came up in 10 responses, you would say that 10 respondants mentioned this along with a concise summary of the issue. Also keep in mind these responses are from a survey about the DC Public Library (DCPL)'},
                {"role": "user", "content": full_message}
                ]
        
                response_content = get_openai_response(key, messages)

                output = response_content
                st.write(output)
