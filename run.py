import os
from app import db
from app import create_app

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        if not os.path.exists('instance/app.db'):
            print("Criando o banco de dados...")
            db.create_all()
            print("Banco de dados criado com sucesso.")

    app.run(debug=True)
