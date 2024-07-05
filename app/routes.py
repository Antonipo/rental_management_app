from flask import render_template, request, redirect, url_for, flash
from app import app, db
from app.models import Person, Property, RentalContract, Payment
from datetime import datetime,timedelta
from sqlalchemy import func

def format_date(date:str):
    fecha_obj = datetime.strptime(date, '%Y-%m-%d')
    fecha_formateada = fecha_obj.strftime('%d/%m/%Y')

    return fecha_formateada

@app.route('/')
def index():
    return redirect(url_for('persons',type='propietario'))

## persons
@app.route('/persons')
@app.route('/persons/<string:type>')
def list_persons(type:str=None):
    if type:
        persons = Person.query.filter(Person.type_person ==type)
    else:
        persons = Person.query.all()
    return render_template('persons/list.html', persons=persons,type=type)

@app.route('/persons/add', methods=['GET', 'POST'])
@app.route('/persons/add/<string:type>', methods=['GET', 'POST'])
def add_person(type:str=None):
    if request.method == 'POST':
        try:
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
            return redirect(url_for('list_persons',type=type))
        except Exception as error:
            flash(f'Error al agregar - msg: {error}', 'danger')
    return render_template('persons/add.html',type=type)

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
        return redirect(url_for('list_persons',type=person.type_person))
    return render_template('persons/edit.html', person=person)

@app.route('/persons/delete/<int:id>', methods=['POST'])
def delete_person(id):
    try:
        person = Person.query.get_or_404(id)
        db.session.delete(person)
        db.session.commit()
        flash('Persona eliminada satisfactoriamente', 'success')
    except Exception as error:
        flash(f'Error al eliminar la persona - msg: {error}', 'danger')
    
    return redirect(url_for('list_persons'))

## routs of properties

@app.route('/properties')
@app.route('/properties/<int:id>')
def list_properties(id:int=None):
    if id:
        person= Person.query.get_or_404(id)
        properties = Property.query.join(Person, Property.owner_id == Person.id).add_columns(
            Property.id,
            Property.name,
            Property.address,
            Property.property_type,
            Property.area,
            Property.available,
            Person.first_name.label('owner_first_name'),
            Person.last_name.label('owner_last_name'),
            Person.id.label('owner_id')
        ).filter(Person.id==id)
    else:
        properties = Property.query.join(Person, Property.owner_id == Person.id).add_columns(
            Property.id,
            Property.name,
            Property.address,
            Property.property_type,
            Property.area,
            Property.available,
            Person.first_name.label('owner_first_name'),
            Person.last_name.label('owner_last_name')
        ).all()
    return render_template('properties/list.html', properties=properties,person=person)

@app.route('/properties/add', methods=['GET', 'POST'])
@app.route('/properties/add/<int:id>', methods=['GET', 'POST'])
def add_property(id:int=None):
    if id:
        persons = Person.query.get_or_404(id)
    else:
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
        return redirect(url_for('list_properties',id=int(request.form['owner_id'])))
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
        return redirect(url_for('list_properties',id=int(request.form['owner_id'])))
    return render_template('properties/edit.html', property=property, persons=persons)

@app.route('/properties/delete/<int:id>', methods=['POST'])
def delete_property(id):
    try:
        property = Property.query.get_or_404(id)
        owner_id = property.owner_id
        db.session.delete(property)
        db.session.commit()
        flash('Propiedad eliminado correctamente', 'success')
    except Exception as error:
        flash(f'Error a eliminar propiedad, msg {error}', 'danger')
        print(error)

    return redirect(url_for('list_properties',id=owner_id))

## routes rental_contract
@app.route('/rental_contracts')
@app.route('/rental_contracts/<int:id>')
def list_rental_contracts(id:int=None):
    if id:
        person = Person.query.get_or_404(id)
        rental_contracts = RentalContract.query.join(Property, Person.id == Property.owner_id).join(RentalContract, Property.id == RentalContract.property_id).add_columns(
            RentalContract.id,
            RentalContract.rent_amount,
            RentalContract.deposit_amount,
            RentalContract.status,
            RentalContract.payment_date,
            RentalContract.start_date,
            RentalContract.end_date,
            Person.first_name.label('tenant_first_name'),
            Person.last_name.label('tenant_last_name'),
            Property.name.label('property_name')
        ).filter(Person.id == id)
        return render_template('rental_contracts/list.html', rental_contracts=rental_contracts,person=person)
    else:
        rental_contracts = RentalContract.query.join(Person, RentalContract.tenant_id == Person.id)\
        .join(Property, RentalContract.property_id == Property.id)\
        .add_columns(
            RentalContract.id,
            RentalContract.rent_amount,
            RentalContract.deposit_amount,
            RentalContract.status,
            RentalContract.payment_date,
            RentalContract.start_date,
            RentalContract.end_date,
            Person.first_name.label('tenant_first_name'),
            Person.last_name.label('tenant_last_name'),
            Property.name.label('property_name')
        ).all()
    return render_template('rental_contracts/list.html', rental_contracts=rental_contracts)

@app.route('/rental_contracts/add', methods=['GET', 'POST'])
@app.route('/rental_contracts/add/<int:id>', methods=['GET', 'POST'])
def add_rental_contract(id:int=None):
    person = Person.query.get_or_404(id)
    tenants = Person.query.filter(Person.type_person =='inquilino')
    properties = Property.query.filter_by(available=True,owner_id=id).all()
    
    if request.method == 'POST':
        person_id = int(request.form['person_id'])
        new_contract = RentalContract(
            tenant_id=int(request.form['tenant_id']),
            property_id=int(request.form['property_id']),
            rent_amount=float(request.form['rent_amount']),
            deposit_amount=float(request.form['deposit_amount']),
            status=request.form['status'],
            payment_date=format_date(request.form['payment_date']),
            start_date=format_date(request.form['start_date']),
            end_date=format_date(request.form['end_date']) if request.form['end_date'] else None
        )
        db.session.add(new_contract)
        db.session.commit()
        
        # Update property availability
        property = Property.query.get(new_contract.property_id)
        property.available = False
        db.session.commit()
        
        flash('Rental contract added successfully', 'success')
        return redirect(url_for('list_rental_contracts',id=person_id))
    
    return render_template('rental_contracts/add.html', tenants=tenants, properties=properties,person=person)

@app.route('/rental_contracts/edit/<int:id>', methods=['GET', 'POST'])
def edit_rental_contract(id):
    contract = RentalContract.query.get_or_404(id)
    tenants = Person.query.all()
    properties = Property.query.all()
    
    if request.method == 'POST':
        contract.tenant_id = int(request.form['tenant_id'])
        contract.property_id = int(request.form['property_id'])
        contract.rent_amount = float(request.form['rent_amount'])
        contract.deposit_amount = float(request.form['deposit_amount'])
        contract.status = request.form['status']
        contract.payment_date = format_date(request.form['payment_date'])
        contract.start_date = format_date(request.form['start_date'])
        contract.end_date = format_date(request.form['end_date']) if request.form['end_date'] else None
        contract.updated_at = datetime.utcnow()
        
        flash('Rental contract updated successfully', 'success')

        if contract.status == 'inactive':
            update_properties = Property.query.get_or_404(contract.property_id)
            update_properties.available = True

        db.session.commit()
        return redirect(url_for('list_rental_contracts'))
    
    return render_template('rental_contracts/edit.html', contract=contract, tenants=tenants, properties=properties)

@app.route('/rental_contracts/delete/<int:id>', methods=['POST'])
def delete_rental_contract(id):
    try:
        contract = RentalContract.query.get_or_404(id)
        property = Property.query.get(contract.property_id)
        property.available = True

        payments_to_delete = Payment.query.filter_by(contract_id=id).all()
        for payment in payments_to_delete:
            db.session.delete(payment)
            
        db.session.delete(contract)
        db.session.commit()
        flash('Rental contract deleted successfully', 'success')
    except Exception as error:
        flash(f'Error al eliminar el contrato - msg: {error}', 'danger')
    
    return redirect(url_for('list_rental_contracts'))

## routes payments
@app.route('/payments')
def list_payments():
    payments = db.session.query(Payment, RentalContract, Property)\
        .join(RentalContract, Payment.contract_id == RentalContract.id)\
        .join(Property, RentalContract.property_id == Property.id)\
        .filter(Payment.status == 'pending')\
        .all()
    return render_template('payments/list.html', payments=payments)

@app.route('/payments/<int:id>/pay', methods=['POST'])
def pay_rent(id):
    payment = Payment.query.get_or_404(id)
    payment.status = 'paid'
    contract= RentalContract.query.get_or_404(payment.contract_id)
    
    # Verificar si el contrato está activo antes de crear el siguiente pago
    if contract.status == 'active':
        # Crear el siguiente pago
        next_payment_date = payment.date + timedelta(days=30)
        next_payment = Payment(
            contract_id=payment.contract_id,
            date=next_payment_date,
            amount=payment.amount,
            status='pending'
        )
        
        db.session.add(next_payment)
        flash('Payment processed successfully and next payment scheduled.', 'success')
    else:
        flash('Payment processed successfully. No new payment scheduled as the contract is not active.', 'info')
    
    db.session.commit()
    
    return redirect(url_for('list_payments'))

# @app.route('/rental_contracts/add', methods=['GET', 'POST'])
# def add_rental_contract():
#     tenants = Person.query.all()
#     properties = Property.query.filter_by(available=True).all()
    
#     if request.method == 'POST':
#         new_contract = RentalContract(
#             tenant_id=int(request.form['tenant_id']),
#             property_id=int(request.form['property_id']),
#             rent_amount=float(request.form['rent_amount']),
#             deposit_amount=float(request.form['deposit_amount']),
#             status=request.form['status'],
#             payment_date=datetime.strptime(request.form['payment_date'], '%d/%m/%Y').date(),
#             start_date=datetime.strptime(request.form['start_date'], '%d/%m/%Y').date(),
#             end_date=datetime.strptime(request.form['end_date'], '%d/%m/%Y').date() if request.form['end_date'] else None
#         )
#         db.session.add(new_contract)
#         db.session.flush()  # This will assign an id to new_contract without committing the transaction
        
#         # Create the first payment
#         first_payment = Payment(
#             contract_id=new_contract.id,
#             date=new_contract.payment_date,
#             amount=new_contract.rent_amount,
#             status='pending'
#         )
#         db.session.add(first_payment)
        
#         # Update property availability
#         property = Property.query.get(new_contract.property_id)
#         property.available = False
        
#         db.session.commit()
        
#         flash('Rental contract added successfully and first payment scheduled.', 'success')
#         return redirect(url_for('list_rental_contracts'))
    
#     return render_template('rental_contracts/add.html', tenants=tenants, properties=properties)
