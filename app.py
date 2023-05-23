from flask import Flask, make_response, request, send_file
import matplotlib.pyplot as plt
import requests
from Service.UploadExcel import storeExcel
from flask_cors import CORS
from docx import Document
from docxtpl import DocxTemplate ,InlineImage
from docx2pdf import convert
import os
import comtypes.client
import docx

app = Flask(__name__)
CORS(app)
CORS(app, resources={r"/*": {"origins": "*"}})

def generate_relation_image(application_id, data):
    application = None
    for item in data:
        if item["applicationSrc"]["id"] == application_id or item["applicationTarget"]["id"] == application_id:
            application = item
            break

    if application is None:
        return None

    applications = set()
    for item in data:
        applications.add(item["applicationSrc"]["appName"])
        applications.add(item["applicationTarget"]["appName"])

    positions = {}
    angle = 0
    angle_increment = 2 * 3.14159 / len(applications)

    for app in applications:
        x = 0.5 + 0.4 * (angle / (2 * 3.14159))
        y = 0.5 + 0.4 * (angle / (2 * 3.14159))
        positions[app] = (x, y)
        angle += angle_increment

    fig, ax = plt.subplots()

    for item in data:
        src_app = item["applicationSrc"]["appName"]
        target_app = item["applicationTarget"]["appName"]
        src_pos = positions[src_app]
        target_pos = positions[target_app]

        if item["flow"] == "INTERNAL":
            arrow_color = 'green'
        else:
            arrow_color = 'red'

        ax.text(src_pos[0], src_pos[1], f'{src_app}\nProtocol: {item["protocol"]}', color='black', ha='center', va='center')

        ax.arrow(src_pos[0], src_pos[1], target_pos[0] - src_pos[0], target_pos[1] - src_pos[1], color=arrow_color, head_width=0.02)

    for app, pos in positions.items():
        circle = plt.Circle(pos, 0.05, color='orange')
        ax.add_artist(circle)

    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.axis('off')

    image_path = f'relations_{application_id}.png'
    plt.savefig(image_path)

    return image_path


@app.route('/api/v1/generate_report/<int:app_id>/<string:type>', methods=['GET'])
def generate_report(app_id,type):
    url = f'http://127.0.0.1:8080/api/v1/applications/{app_id}'
    response = requests.get(url)
    if response.status_code == 200:
        variables_json = response.json()
    url_assessment = f'http://127.0.0.1:8080/api/v1/applications/{app_id}/assessment'
    response1 = requests.get(url_assessment)
    if response.status_code == 200:
        variables_json1 = response1.json()
    response = requests.get(f'http://127.0.0.1:8080/api/v1/interfaces')
    if response.status_code == 200:
        data = response.json()

    image_path = generate_relation_image(app_id, data)

    comtypes.CoInitialize()
    doc = DocxTemplate("./Ressources/template_v2.docx")
    grouped_questions = {}

    for step in variables_json1['steps']:
        for category in step['categories']:
            if category['category'] in ['Application Overview', 'Availability & Business Continuity', 'End User Information', 'Infrastructure Supporting Components', 'Requirements & Constraints', 'Non-Production Information', 'Product & Vendor Information']:
                 if category['category'] in grouped_questions:
                     grouped_questions[category['category']].extend(category['questions'])
                 else:
                    grouped_questions[category['category']] = category['questions']
                    


    context = {
        'watermark':"Archimaster",
        'client':variables_json['appName'],
        'description': variables_json['appDescription'],
        'name': variables_json['appName'],
        'relations_image':InlineImage(doc, 'relations_102.png'),


        'servers': [
        {
            "currentDiskGb": server['currentDiskGb'],
            "currentNumberOfCores":  server['currentNumberOfCores'],
            "currentRamGb": server['currentRamGb'],
            "datacenter": server['datacenter'],
            "environment":  server['environment'],
            "ipAddress": server['ipAddress'],
            "operatingSystem": server['operatingSystem'],
            "role":  server['role'],
            "serverName": server['serverName'],
            "type":  server['type'],

        }
        for server in variables_json['servers']
    ],
        'Contacts': [
        {
            'fullName': contact['fullName'],
            'title': contact['title'],
            'department': contact['department'], 
            'email': contact['email']
        }
        for contact in variables_json['contacts']
    ],
    'Assessment': {
    'id': variables_json1['id'],
    'assessment': variables_json1['assessment'],
    'createdAt': variables_json1['createdAt'],
    'note': variables_json1['note'],
    'groupedQuestions': grouped_questions
},
    'databases': [],
}
    for server in variables_json['servers']:
        server_name = server['serverName']
        for database in server['databaseList']:
            database_name = database['databaseName']
            context["databases"].append({
                "serverName": server_name,
                "databaseName": database_name
            })

    doc.render(context)
    doc.save("document_rempli.docx")
    if type=="pdf" :
        input_file = 'document_rempli.docx'
        output_file = 'document.pdf'
        doc = docx.Document(input_file)
        # Save the Word document as a PDF using Microsoft Word
        word = comtypes.client.CreateObject("Word.Application")
        docx_path = os.path.abspath(input_file)
        pdf_path = os.path.abspath(output_file)
        pdf_format = 17  # PDF file format code
        word.Visible = False
        in_file = word.Documents.Open(docx_path)
        in_file.SaveAs(pdf_path, FileFormat=pdf_format)
        in_file.Close()
        word.Quit()

        response = make_response(send_file('document.pdf'))
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=report2.pdf'

        return response
    
    file_path = os.path.abspath('document_rempli.docx')
    file_name = 'document_rempli.docx'
    response = make_response(send_file(file_path, as_attachment=True))
    response.headers['Content-Disposition'] = f'attachment; filename="{file_name}"'
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

    return response






@app.route('/api/v1/upload', methods=['POST'])
def upload_excel():
    files = request.files.getlist('file')   
    return storeExcel(files)    


#-------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)