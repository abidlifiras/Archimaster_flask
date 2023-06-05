import requests
from sqlalchemy import create_engine
import pandas as pd
import yaml
import re

def clean_column_names(df):
    """Nettoyer les noms de colonnes d'un DataFrame."""
    regex = r'[^a-zA-Z0-9_]+'
    new_columns = [re.sub(regex, '_', col.strip()) for col in df.columns]
    df.columns = new_columns
    
    return df

def store_excel(files):
    with open('Ressources/configDB.yml', 'r') as f:
        configDB = yaml.safe_load(f)
    config = configDB.get('mysql', [])
    engine = create_engine(f"mysql://{config['user']}:{config['password']}@{config['host']}/{config['database']}")
    
    for file in files:
        xl_file = pd.ExcelFile(file)
        for sheet_name in xl_file.sheet_names:
            sheet_data = xl_file.parse(sheet_name)
            if sheet_data.columns.nlevels > 1:
                continue
            else:
                df = clean_column_names(sheet_data)
                query = f"SELECT MAX(id) FROM {sheet_name}"
                max_id_df = pd.read_sql_query(query, engine)
                max_id = max_id_df.iloc[0, 0]
                if pd.isna(max_id):
                    start_id = 1
                else:
                    start_id = int(max_id) + 1
                ids = range(start_id, start_id + len(df))
                df['id'] = ids   
                df.head()
                df.to_sql(sheet_name, engine, if_exists="append", index=False)
                if(sheet_name == 'applications'):
                      for id in ids :
                        url_assessment = f"http://127.0.0.1:8080/api/v1/applications/{id}/addAssessment/52"
                        requests.post(url_assessment)
    
    return "File(s) Upload Successful"
