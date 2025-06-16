### 🧠 **COLA: Comandos do Flask-Migrate**

#### 📦 Instalar (uma vez)

```bash
pip install Flask-Migrate
```

#### 🛠️ Iniciar migrações (apenas 1 vez no projeto)

```bash
flask db init
```

#### 🆕 Sempre que mudar os models

```bash
flask db migrate -m "descrição da mudança"
```

#### ⬆️ Aplicar as mudanças no banco

```bash
flask db upgrade
```

#### 🔁 (Opcional) Voltar para a versão anterior

```bash
flask db downgrade
```

### ⚙️ Variáveis no `.flaskenv`

```env
FLASK_APP=app:create_app
FLASK_ENV=development
```
