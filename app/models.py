from app import db
from datetime import datetime

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dni=db.Column(db.String(10), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    nationality  = db.Column(db.String(100), nullable=False)
    type_person = db.Column(db.String(100), nullable=True)
    
    # Agregar más campos según sea necesario

class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(200), nullable=False)
    property_type  = db.Column(db.String(50))
    area = db.Column(db.Float)
    description = db.Column(db.Text)
    available *true o false
    persona.id *


class RentalContract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    persona_id = db.Column(db.Integer, db.ForeignKey('persona.id'), nullable=False)
    inmueble_id = db.Column(db.Integer, db.ForeignKey('inmueble.id'), nullable=False)
    rent_amount = db.Column(db.Float, nullable=False) formato ######.####
    deposit_amount = db.Column(db.Float), formato ######.####
    status = db.Column(db.String(20), default='active')
    paymet_date
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)

    # Agregar más campos según sea necesario

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contrato.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    # Agregar más campos según sea necesario
