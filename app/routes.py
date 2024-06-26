from flask import render_template, request, redirect, url_for, flash
from app import app, db
from app.models import Person, Property, RentalContract, Payment
from datetime import datetime

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/persons')
def list_persons():
    persons = Person.query.all()
    return render_template('persons/list.html', persons=persons)

@app.route('/persons/add', methods=['GET', 'POST'])
def add_person():
    if request.method == 'POST':
        new_person = Person(
            dni=request.form['dni'],
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            phone_number=request.form['phone_number'],
            address=request.form['address'],
            nationality=request.form['nationality'],
            type_person=request.form['type_person']
        )
        db.session.add(new_person)
        db.session.commit()
        flash('Person added successfully', 'success')
        return redirect(url_for('list_persons'))
    return render_template('persons/add.html')

@app.route('/persons/edit/<int:id>', methods=['GET', 'POST'])
def edit_person(id):
    person = Person.query.get_or_404(id)
    if request.method == 'POST':
        person.dni = request.form['dni']
        person.first_name = request.form['first_name']
        person.last_name = request.form['last_name']
        person.phone_number = request.form['phone_number']
        person.address = request.form['address']
        person.nationality = request.form['nationality']
        person.type_person = request.form['type_person']
        person.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Person updated successfully', 'success')
        return redirect(url_for('list_persons'))
    return render_template('persons/edit.html', person=person)

@app.route('/persons/delete/<int:id>', methods=['POST'])
def delete_person(id):
    person = Person.query.get_or_404(id)
    db.session.delete(person)
    db.session.commit()
    flash('Person deleted successfully', 'success')
    return redirect(url_for('list_persons'))

## routs of properties

@app.route('/properties')
def list_properties():
    properties = Property.query.all()
    return render_template('properties/list.html', properties=properties)

@app.route('/properties/add', methods=['GET', 'POST'])
def add_property():
    persons = Person.query.all()
    if request.method == 'POST':
        new_property = Property(
            name=request.form['name'],
            address=request.form['address'],
            property_type=request.form['property_type'],
            area=float(request.form['area']),
            description=request.form['description'],
            available=request.form.get('available') == 'on',
            owner_id=int(request.form['owner_id'])
        )
        db.session.add(new_property)
        db.session.commit()
        flash('Property added successfully', 'success')
        return redirect(url_for('list_properties'))
    return render_template('properties/add.html', persons=persons)

@app.route('/properties/edit/<int:id>', methods=['GET', 'POST'])
def edit_property(id):
    property = Property.query.get_or_404(id)
    persons = Person.query.all()
    if request.method == 'POST':
        property.name = request.form['name']
        property.address = request.form['address']
        property.property_type = request.form['property_type']
        property.area = float(request.form['area'])
        property.description = request.form['description']
        property.available = request.form.get('available') == 'on'
        property.owner_id = int(request.form['owner_id'])
        property.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Property updated successfully', 'success')
        return redirect(url_for('list_properties'))
    return render_template('properties/edit.html', property=property, persons=persons)

@app.route('/properties/delete/<int:id>', methods=['POST'])
def delete_property(id):
    property = Property.query.get_or_404(id)
    db.session.delete(property)
    db.session.commit()
    flash('Property deleted successfully', 'success')
    return redirect(url_for('list_properties'))

# Agregar rutas para personas, inmuebles, contratos y pagos