import pandas as pd
import numpy as np

# Créer un DataFrame aléatoire pour chaque vecteur
labels = ['revise', 'retain', 'rehost', 'rebuild', 'rearchitect', 'remain', 'replace']
vectors = ['benefit', 'risk', 'effort']
num_options = 145

data = np.random.randint(1, 4, size=(len(labels), num_options))
df_benefit = pd.DataFrame(data, index=labels, columns=range(1, num_options + 1))
df_risk = pd.DataFrame(data, index=labels, columns=range(1, num_options + 1))
df_effort = pd.DataFrame(data, index=labels, columns=range(1, num_options + 1))

# Créer un fichier Excel et écrire les DataFrames dans les feuilles de calcul correspondantes
excel_file = 'Ressources/score.xlsx'
with pd.ExcelWriter(excel_file) as writer:
    df_benefit.to_excel(writer, sheet_name='benefit')
    df_risk.to_excel(writer, sheet_name='risk')
    df_effort.to_excel(writer, sheet_name='effort')

print("Le fichier Excel a été créé avec succès.")
