import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import yaml
from sklearn import preprocessing
from flask import send_file
import matplotlib.pyplot as plt

def calculate_scores(app_id, detailed):
    engine = create_engine('mysql+pymysql://root:firas@localhost/cra')
    df_assessment_response = pd.read_sql_table('assessment_response', engine)

    with open('./Ressources/scoring.yml', 'r') as file:
        data = yaml.safe_load(file)

    filtered_df = df_assessment_response.loc[df_assessment_response['app_id'] == app_id]
    df_options = pd.read_sql_table('options', engine)
    list_id_options=[]
    for index, row in filtered_df.iterrows():
        for _, df_op in df_options.iterrows():
            if row['response'] == df_op['option']:
                 list_id_options.append(df_op['id'])

    labels = ['revise','retain','rehost','rebuild','rearchitect','remain','replace']
    vectors = ['benefit', 'effort', 'risk']
    matrix = pd.DataFrame(0, index=labels, columns=vectors)
    label_descriptions = {
        "revise": "The 'revise' migration strategy involves making significant modifications or adjustments to the existing system before migrating it to the cloud.",
        "retain": "The 'retain' migration strategy focuses on keeping the current system as it is, without any significant changes, while moving it to the cloud infrastructure.",
        "rehost": "The 'rehost' migration strategy, also known as 'lift and shift,' involves moving the existing system to the cloud without making significant changes to its architecture.",
        "rebuild": "The 'rebuild' migration strategy entails rebuilding the system from scratch using cloud-native technologies and architectures.",
        "rearchitect": "The 'rearchitect' migration strategy involves making significant architectural changes to the system to optimize it for cloud environments.",
        "remain": "The 'remain' migration strategy refers to keeping the system in its current state without migrating it to the cloud.",
        "replace": "The 'replace' migration strategy involves replacing the existing system with a new system or solution in the cloud."
    }
    
    for question_entry in data:
        option_id = question_entry['option_id']
        if option_id in list_id_options :
            for label_entry in question_entry['labels']:
                label = label_entry['label']
                for vector in vectors:
                    weight = label_entry[vector]
                    matrix.loc[label, vector] += weight

    normalized_matrix = preprocessing.normalize(matrix, norm='l2', axis=0)
    criteria = [0.6, -0.5,-0.4 ]
    weighted_normalized_matrix = normalized_matrix * criteria
    ideal_best = np.max(weighted_normalized_matrix, axis=0)
    ideal_worst = np.min(weighted_normalized_matrix, axis=0)
    distance_best = np.sqrt(np.sum((weighted_normalized_matrix - ideal_best) ** 2, axis=1))
    distance_worst = np.sqrt(np.sum((weighted_normalized_matrix - ideal_worst) ** 2, axis=1))
    scores = distance_worst / (distance_worst + distance_best)
    
    recommended_label = labels[np.argmax(scores)]
    
    if detailed == 1:
        plt.figure()
        colors = plt.cm.viridis(scores)  # Utilisation de la palette de couleurs viridis
        plt.bar(labels, scores, color=colors)
        plt.xlabel('Strategies')
        plt.ylabel('Scores')
        plt.title(f'Recommended strategy : {recommended_label}')
        plt.xticks(rotation='vertical')
        plt.tight_layout()  # Ajustement automatique des marges
        image_path = f"application{app_id}.png"
        plt.savefig(image_path)
        
        return send_file(image_path, mimetype='image/png')
    if detailed==2 :
        plt.figure()
        colors = plt.cm.viridis(scores)  # Utilisation de la palette de couleurs viridis
        plt.bar(labels, scores, color=colors)
        plt.xlabel('Strategies')
        plt.ylabel('Scores')
        plt.title(f'Recommended strategy : {recommended_label}')
        plt.xticks(rotation='vertical')
        plt.tight_layout()  # Ajustement automatique des marges
        image_path = f"application{app_id}.png"
        plt.savefig(image_path)
        return({recommended_label:label_descriptions[recommended_label]},image_path)

    return {recommended_label:label_descriptions[recommended_label]}