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


def storeExcel(files):
    with open('Ressources/configDB.yml', 'r') as f:
        configDB = yaml.safe_load(f)
    config=configDB.get('mysql',[])
    engine = create_engine(f"mysql://{config['user']}:{config['password']}@{config['host']}/{config['database']}")
    for file in files:
        xl_file = pd.ExcelFile(file)
        for sheet_name in xl_file.sheet_names:
            sheet_data = xl_file.parse(sheet_name)
            # pivot table
            if sheet_data.columns.nlevels > 1:
                continue
            else :
                df = clean_column_names(sheet_data)
                df.head()
                df.to_sql(sheet_name, engine, if_exists="append", index=False)
    return "File(s) Upload Successful"
