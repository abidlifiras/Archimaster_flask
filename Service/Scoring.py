from flask import send_file
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist

import yaml

def calculate_scores(app_id):
    engine = create_engine('mysql+pymysql://root:firas@localhost/cra')
    df_assessment_response = pd.read_sql_table('assessment_response', engine)

    with open('./Ressources/scoring.yml', 'r') as file:
        data = yaml.safe_load(file)

    filtered_df = df_assessment_response.loc[df_assessment_response['app_id'] == app_id]
    question_ids_yml = [int(entry['question_id']) for entry in data]
    filtered_df = filtered_df[filtered_df['question_id'].isin(question_ids_yml)]

    label_scores = {}
    for _, row in filtered_df.iterrows():
        question_id = int(row['question_id'])
        labels = data[question_id-1]['labels']
        for label in labels:
            label_name = label['label']
            risk = label['risk']
            benefit = label['benefit']
            effort = label['effort']

            if label_name not in label_scores:
                label_scores[label_name] = {'risk': [], 'benefit': [], 'effort': []}

            label_scores[label_name]['risk'].append(risk)
            label_scores[label_name]['benefit'].append(benefit)
            label_scores[label_name]['effort'].append(effort)

    selected_label = None
    max_benefit = -1
    min_effort = float('inf')
    min_risk = float('inf')

    for label, scores in label_scores.items():
        risks = scores['risk']
        benefits = scores['benefit']
        efforts = scores['effort']

        if max(benefits) > max_benefit or (max(benefits) == max_benefit and min(efforts) < min_effort) or (max(benefits) == max_benefit and min(efforts) == min_effort and min(risks) < min_risk):
            selected_label = label
            max_benefit = max(benefits)
            min_effort = min(efforts)
            min_risk = min(risks)

    selected_label_scores = pd.DataFrame(label_scores[selected_label])

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes = axes.flatten()

    combinations = [('effort', 'benefit'), ('benefit', 'risk'), ('risk', 'effort')]
    top_categories = sorted(label_scores, key=lambda x: max(label_scores[x]['benefit']), reverse=True)[:3]
    colors = ['red', 'green', 'blue']

    for i, ax in enumerate(axes):
        x_label, y_label = combinations[i]
        ax.set_xlabel(x_label.capitalize())
        ax.set_ylabel(y_label.capitalize())
        ax.set_title(selected_label)

        for label, scores in label_scores.items():
            x_values = np.array(scores[x_label])
            y_values = np.array(scores[y_label])

            if label == selected_label:
                ax.scatter(np.mean(x_values), np.mean(y_values), c='red', label=label, marker='o')

        ax.legend()

    plt.tight_layout()
    image_path = f"application{app_id}.png"
    plt.savefig(image_path)

    return send_file(image_path, mimetype='image/png')
