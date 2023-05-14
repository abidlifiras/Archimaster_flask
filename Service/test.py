from io import BytesIO
import os
from flask import Flask, make_response, request
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph,Frame, Spacer, Table, TableStyle,Image,KeepTogether
from sqlalchemy import create_engine
from reportlab.lib.colors import Color, black, gray
from Service.UploadExcel import storeExcel
from reportlab.lib.styles import ParagraphStyle
from flask_cors import CORS




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:firas@localhost/cra'
db = SQLAlchemy(app)
CORS(app)
CORS(app, resources={r"/*": {"origins": "*"}})


class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    app_name = db.Column(db.String(255))
    app_description = db.Column(db.String(255))
    server = db.relationship('Server', secondary='server_application', backref='app_servers')
    



class Server(db.Model):
    __tablename__ = 'servers'
    id = db.Column(db.Integer, primary_key=True)
    server_name = db.Column(db.String(255))
    ip_address = db.Column(db.String(255))
    operating_system = db.Column(db.String(255))
    applications = db.relationship('Application',secondary='server_application',backref=db.backref('server_apps', lazy=True))    
    databases = db.relationship('Database',secondary='server_database',backref=db.backref('server_Db', lazy=True))    


class Database(db.Model):
    __tablename__ = 'base_de_donnee'
    database_id = db.Column(db.Integer, primary_key=True)
    database_name = db.Column(db.String(255))
    database_version = db.Column(db.String(255))
    servers = db.relationship('Server', secondary='server_database', backref='Db_servers')


class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    department = db.Column(db.String(255))
    applications = db.relationship('Application', secondary='application_contact', backref='contacts')


class ServerApplication(db.Model):
    __tablename__ = 'server_application'
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'))
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'))


class ServerDatabase(db.Model):
    __tablename__ = 'server_database'
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'))
    database_id = db.Column(db.Integer, db.ForeignKey('base_de_donnee.database_id'))


class ContactApplication(db.Model):
    __tablename__ = 'application_contact'
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'))
    
class Assessment(db.Model):
    __tablename__ = 'assessments'
    id = db.Column(db.Integer, primary_key=True)
    Assessment = db.Column(db.String(255))
    note = db.Column(db.String(255))
    
class AssessmentResponse(db.Model):
    __tablename__ = 'assessment_response'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    response = db.Column(db.String(255))

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(255))
    questions = db.relationship('Question', backref='category')

class Option(db.Model):
    __tablename__ = 'options'
    id = db.Column(db.Integer, primary_key=True)
    option = db.Column(db.String(255))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    
class Step(db.Model):
    __tablename__ = 'steps'
    id = db.Column(db.Integer, primary_key=True)
    step = db.Column(db.String(255))
    
        

@app.route('/api/v1/generate_report/<int:app_id>', methods=['GET'])
def generate_report(app_id):
    engine = create_engine('mysql+pymysql://root:firas@localhost/cra')
    df_assessment_response = pd.read_sql_table('assessment_response', engine)
    df_assessments = pd.read_sql_table('assessments', engine)
    df_categories = pd.read_sql_table('categories', engine)
    df_questions = pd.read_sql_table('questions', engine)
    df_steps = pd.read_sql_table('steps', engine)
    df_options=pd.read_sql_table('options',engine)
    
    df_assessments_steps = pd.merge(df_assessments, df_steps, left_on='id', right_on='assessment_id', how='inner')

    df_steps_categories = pd.merge(df_steps, df_categories, left_on='id', right_on='step_id', how='inner')

    df_categories_questions = pd.merge(df_categories, df_questions, left_on='id', right_on='category_id', how='inner')

    # Filtrer df_assessment_response pour l'application spécifiée
    df_assessment_response = df_assessment_response[df_assessment_response['app_id'] == app_id]
    
    df_options_questions=pd.merge(df_options, df_questions, left_on='question_id', right_on='id', how='inner')


    table_style= [('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
             ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
             ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
             ('BACKGROUND', (0, 0), (-1, 0), colors.gray)]  
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    x = 100 
    y = 700  
    image_path = "./Resources/orange-logo.svg"
    c.drawImage(image_path, x, y, width=2*inch, height=2*inch)
    y -= 2*inch
      
    app_data = Application.query.filter_by(id=app_id).first()
    server_data = Server.query.join(ServerApplication).join(Application).filter(Application.id == app_id).all()
    db_data = Database.query.join(ServerDatabase).join(Server).join(ServerApplication).join(Application).filter(Application.id == app_id).all()
    contact_data = Contact.query.join(ContactApplication).join(Application).filter(Application.id == app_id).all()
    elements = []
    styles = getSampleStyleSheet()
    style_title = styles["Title"]
    style_body = styles["BodyText"]
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x, y, "Rapport For Application {}".format(app_data.app_name.upper()))
    y -= 20  
      
    c.setFont("Helvetica", 12)
    c.drawString(x, y, "Description: {}".format(app_data.app_description))
    y -= 20
    
    # Servers table
    c.setFont("Helvetica", 12)
    c.drawPara()
    y -= 20
    elements.append(Paragraph("Servers :", style_body))
    if server_data:
        server_table_data = [['Server Name', 'Adresse IP', 'Operating Sysytem']]
        for server in server_data:
            server_table_data.append([server.server_name, server.ip_address, server.operating_system])
        server_table = Table(server_table_data)
        server_table.setStyle(TableStyle(table_style))
        elements.append(server_table)   
    else:
        elements.append(Paragraph("No Servers found" , style_body))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Databases :", style_body))
        # BD table
    if db_data:
        db_table_data = [['Nom du Database', 'Version']]
        for db in db_data:
            db_table_data.append([db.database_name, db.database_version])
        db_table = Table(db_table_data)
        db_table.setStyle(TableStyle(table_style))

        elements.append(db_table)
    else:
        elements.append(Paragraph("No Databases found", style_body))
        
    
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Contacts :", style_body))
           # contact table
    if contact_data:
        contact_table_data = [['Full Name', 'Email ','Department']]
        for contact in contact_data:
            contact_table_data.append([contact.full_name, contact.email,contact.department])
        contact_table = Table(contact_table_data)
        contact_table.setStyle(TableStyle(table_style))
        elements.append(contact_table)

    else:
        elements.append(Paragraph("No Contacts found", style_body))
    
    # Assessment table
    assessment_name_displayed = False
    step_name_displayed = False
    category_name_displayed = False

    for index, assessment_row in df_assessments_steps.iterrows():
        assessment_name = assessment_row['assessment']
        step_name = assessment_row['step_y']
        step_name_displayed=False
        if not assessment_name_displayed:
            
            style_body.fontName = "Helvetica"  
            style_body.fontSize = 12  # Taille de la police
            style_body.textColor = colors.black  # Couleur du texte
            style_body.alignment = 1  # Alignement (0: à gauche, 1: centré, 2: à droite)
            style_body.spaceAfter = 0  # Espace après le paragraphe
            style_body.spaceBefore = 0  # Espace avant le paragraphe
            style_body.leftIndent = 20  # Retrait à gauche du paragraphe
            style_body.rightIndent = 20  # Retrait à droite du paragraphe
            style_body.firstLineIndent = 10
            elements.append(Paragraph(f"Assessment: {assessment_name}", style_body))
            assessment_name_displayed = True

        for _, category_row in df_steps_categories.iterrows():
            category_name = category_row['category']
            category_name_displayed=False
            if category_row['step_id'] == assessment_row['id_y']:
                for _, question_row in df_categories_questions.iterrows():
                    question_text = question_row['question']
                    question_id = question_row['id_y']
                    if question_row['category_id'] == category_row['id_y']:
                        response = df_assessment_response[(df_assessment_response['question_id'] == question_id) &
                                                        (df_assessment_response['app_id'] == app_id)]['response'].values
                        if len(response) > 0:
                            response_text = response[0]
                            if not step_name_displayed :
                                elements.append(Paragraph(f"Step: {step_name}", style_body))
                                step_name_displayed=True
                            if not category_name_displayed :
                                elements.append(Paragraph(f"Category: {category_name}", style_body))
                                category_name_displayed=True
                            elements.append(Paragraph(f"Question: {question_text}", style_body))

                            question_type = question_row['type']
                            if question_type == 'radio_group':
                                options = df_options_questions[df_options_questions['question_id'] == question_id]['option'].values
                                choices = list(options)
                                radio_button_icon_path = "./Ressources/radio_groupe.png"
                                checked_radio_button_icon_path = "./Ressources/checked.png"

                                radio_button_icon_size = 7 
                                table_data = []

                                for choice in choices:
                                    if choice == response_text:
                                        radio_button_icon = Image(checked_radio_button_icon_path, width=radio_button_icon_size, height=radio_button_icon_size)
                                    else:
                                        radio_button_icon = Image(radio_button_icon_path, width=radio_button_icon_size, height=radio_button_icon_size)
                                    
                                    table_row = [radio_button_icon, choice]
                                    table_data.append(table_row)

                                table = Table(table_data)
                                elements.append(table)
                            else:
                                elements.append(Spacer(1, 12))
                                paragraph=Paragraph(f" {response_text}", style=ParagraphStyle('My Para style',fontName='Times-Roman',backColor='#F1F1F1',fontSize=12,borderWidth=1,borderPadding=(10,10,10),leading=10,alignment=0))
                                elements.append(paragraph)
                                elements.append(Spacer(1, 12))




    pdf = SimpleDocTemplate(buffer,pagesize=letter)
    pdf.build(elements)
    
    buffer.seek(0)
    pdf_data = buffer.getvalue()

    response = make_response(pdf_data)

    # Définir les en-têtes pour indiquer qu'il s'agit d'un fichier PDF
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=report2.pdf'
    file_path = os.path.join(os.getcwd(), 'report.pdf')
    with open(file_path, 'wb') as f:
        f.write(buffer.getvalue())
    return response




@app.route('/api/v1/upload', methods=['POST'])
def upload_excel():
    files = request.files.getlist('file')   
    return storeExcel(files)    


#-------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)