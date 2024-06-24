from flask import render_template, request, jsonify
from app import app, db
from app.models import Persona, Inmueble, Contrato, Pago

@app.route('/')
def index():
    return render_template('index.html')

# Agregar rutas para personas, inmuebles, contratos y pagos