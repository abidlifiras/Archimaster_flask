from flask import Flask, make_response, request, send_file
import requests
from Service.UploadExcel import storeExcel
from flask_cors import CORS
from docx import Document
from docxtpl import DocxTemplate
from docx2pdf import convert
import os
import comtypes.client
import docx

app = Flask(__name__)
CORS(app)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/v1/generate_report/<int:app_id>', methods=['GET'])
def generate_report(app_id):
    url = f'http://127.0.0.1:8080/api/v1/applications/{app_id}'
    response = requests.get(url)
    if response.status_code == 200:
        variables_json = response.json()
    url_assessment = f'http://127.0.0.1:8080/api/v1/applications/{app_id}/assessment'
    response1 = requests.get(url_assessment)
    if response.status_code == 200:
        variables_json1 = response1.json()

    comtypes.CoInitialize()
    doc = DocxTemplate("./Ressources/template_v2.docx")

    context = {
        'client':variables_json['appName'],
        'description': variables_json['appDescription'],
        'name': variables_json['appName'],
        'Contacts': [
        {
            'fullName': contact['fullName'],
            'title': contact['title'],
            'department': contact['department'],  # Remplacez 'N/A' par le champ de téléphone approprié
            'email': contact['email']
        }
        for contact in variables_json['contacts']
    ],
    'steps': [
        {
            'id': step['id'],
            'step': step['step'],
            'categories': [
                {
                    'id': category['id'],
                    'category': category['category'],
                    'createdAt': category['createdAt'],
                    'deletedAt': category['deletedAt'],
                    'modifiedAt': category['modifiedAt'],
                    'questions': [
                        {
                            'id': question['id'],
                            'required': question['required'],
                            'question': question['question'],
                            'deletedAt': question['deletedAt'],
                            'modifiedAt': question['modifiedAt'],
                            'createdAt': question['createdAt'],
                            'type': question['type'],
                            'options': [
                                {
                                    'id': option['id'],
                                    'isActive': option['isActive'],
                                    'option': option['option'],
                                    'deletedAt': option['deletedAt'],
                                    'modifiedAt': option['modifiedAt'],
                                    'createdAt': option['createdAt']
                                }
                                for option in question['options']
                            ],
                            'response': question['response']
                        }
                        for question in category['questions']
                    ]
                }
                for category in step['categories']
            ]
        }
        for step in variables_json1['steps']
    ]
}


    doc.render(context)
    doc.save("document_rempli.docx")

    return variables_json






@app.route('/api/v1/upload', methods=['POST'])
def upload_excel():
    files = request.files.getlist('file')   
    return storeExcel(files)    


#-------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)