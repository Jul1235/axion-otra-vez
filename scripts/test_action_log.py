import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db, Usuario, ActionHistory
from werkzeug.security import generate_password_hash

with app.app_context():
    print('App context ready')
    try:
        db.create_all()
    except Exception as e:
        print('create_all error:', e)

    email = 'testbot@example.com'
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        usuario = Usuario(nombre='Test Bot', email=email, password=generate_password_hash('Test1234'))
        db.session.add(usuario)
        db.session.commit()
        print('Created test user', usuario.ID_Users)
    else:
        print('Test user exists', usuario.ID_Users)

    client = app.test_client()

    # Login
    rv = client.post('/login', data={'email': email, 'password': 'Test1234'}, follow_redirects=True)
    print('Login status:', rv.status_code)

    # Send a log action
    resp = client.post('/api/log_action', json={'accion': 'test_action_from_script', 'producto_id': None, 'nombre': 'Prueba'}, headers={'Content-Type': 'application/json'})
    print('POST /api/log_action ->', resp.status_code, resp.get_data(as_text=True))

    # Query last actions for user
    acts = ActionHistory.query.filter_by(ID_Users=usuario.ID_Users).order_by(ActionHistory.fecha.desc()).limit(5).all()
    print('Last actions for user:')
    for a in acts:
        print('-', a.ID_Action, a.accion, a.nombre, a.fecha)

    # Print total count
    total = ActionHistory.query.filter_by(ID_Users=usuario.ID_Users).count()
    print('Total actions for user in DB:', total)
