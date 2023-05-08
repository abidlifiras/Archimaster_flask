from io import BytesIO
import os
from flask import Flask, make_response, request
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from Service.UploadExcel import storeExcel
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

        

@app.route('api/v1/generate_report/<int:app_id>', methods=['GET'])
def generate_report(app_id):
    table_style=[('ALIGN',(1,1),(-2,-2),'RIGHT'),
                       ('TEXTCOLOR',(1,1),(-2,-2),colors.white),
                       ('VALIGN',(0,0),(0,-1),'TOP'),
                       ('TEXTCOLOR',(0,0),(0,-1),colors.black),
                       ('ALIGN',(0,-1),(-1,-1),'CENTER'),
                       ('VALIGN',(0,-1),(-1,-1),'MIDDLE'),
                       ('TEXTCOLOR',(0,-1),(-1,-1),colors.black),
                       ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                       ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                       ]
    
    app_data = Application.query.filter_by(id=app_id).first()
    server_data = Server.query.join(ServerApplication).join(Application).filter(Application.id == app_id).all()
    db_data = Database.query.join(ServerDatabase).join(Server).join(ServerApplication).join(Application).filter(Application.id == app_id).all()
    contact_data = Contact.query.join(ContactApplication).join(Application).filter(Application.id == app_id).all()
    elements = []
    styles = getSampleStyleSheet()
    style_title = styles["Title"]
    style_body = styles["BodyText"]
    elements.append(Paragraph("RAPPORT POUR L'APPLICATION {}".format(app_data.app_name.upper()), style_title))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Description de l'application : {}".format(app_data.app_description), style_body))
    buffer = BytesIO()
    # Servers table
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Serveurs :", style_body))
    if server_data:
        server_table_data = [['Nom du serveur', 'Adresse IP', 'Système d\'exploitation']]
        for server in server_data:
            server_table_data.append([server.server_name, server.ip_address, server.operating_system])
        server_table = Table(server_table_data)
        server_table.setStyle(TableStyle(table_style))
        elements.append(server_table)   
    else:
        elements.append(Paragraph("Aucun serveur trouvé ", style_body))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Bases de données :", style_body))
        # BD table
    if db_data:
        db_table_data = [['Nom du Database', 'Version']]
        for db in db_data:
            db_table_data.append([db.database_name, db.database_version])
        db_table = Table(db_table_data)
        db_table.setStyle(TableStyle(table_style))

        elements.append(db_table)
    else:
        elements.append(Paragraph("Aucun Database trouvé.", style_body))
        
    
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("Contacts :", style_body))
           # contact table
    if contact_data:
        contact_table_data = [['Nom complet', 'Email ','Département']]
        for contact in contact_data:
            contact_table_data.append([contact.full_name, contact.email,contact.department])
        contact_table = Table(contact_table_data)
        contact_table.setStyle(TableStyle(table_style))
        elements.append(contact_table)


    else:
        elements.append(Paragraph("Aucun Contact trouvé.", style_body))
        
    pdf = SimpleDocTemplate(buffer)
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




@app.route('api/v1/upload', methods=['POST'])
def upload_excel():
    files = request.files.getlist('file')   
    return storeExcel(files)    


#-------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)