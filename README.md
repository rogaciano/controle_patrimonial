# Controle Patrimonial

## Configuração local

### 1. Criar o arquivo de ambiente

Copie o exemplo para um arquivo local real:

```powershell
Copy-Item .env.example .env
```

Edite o arquivo [.env](.env) com as credenciais adequadas para o seu ambiente.

### 2. Subir o banco PostgreSQL com Docker

```powershell
docker compose up -d db_sertamol
```

### 3. Instalar dependências

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Rodar as migrações

```powershell
python manage.py migrate
```

### 5. Criar superusuário (opcional)

```powershell
python manage.py createsuperuser
```

### 6. Iniciar o projeto

```powershell
python manage.py runserver
```

## Observações

- O arquivo [.env](.env) não deve ser enviado ao Git.
- O arquivo [.env.example](.env.example) serve como modelo seguro para compartilhamento.
