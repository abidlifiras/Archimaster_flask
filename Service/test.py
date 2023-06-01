import pandas as pd
from sqlalchemy import create_engine
import yaml

def calculate(app_id) :
    engine = create_engine('mysql+pymysql://root:firas@localhost/cra')
    df_assessment_response = pd.read_sql_table('assessment_response', engine)

    filtered_df = df_assessment_response.loc[df_assessment_response['app_id'] == app_id]
    with open('./Ressources/scoring.yml', 'r') as file:
        data = yaml.safe_load(file)
    label_scores = {}
    for _, row in filtered_df.iterrows():
        question_id = int(row['question_id'])
        print (question_id)
        labels = data[question_id]['labels']
    
    
calculate(52)