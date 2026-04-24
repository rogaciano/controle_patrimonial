# Guia de Deploy para a Instância `jamoto` (`jamoto.gestorpatrimonial.com.br`)

Como criamos os arquivos locais `nginx_jamoto.conf` e `gunicorn_jamoto.service`, o primeiro passo é fazer o `git add`, `git commit` e `git push` do seu repositório local para que esses arquivos cheguem ao servidor.

Após o push, **conecte-se via SSH ao seu VPS** e siga as instruções abaixo:

---

## Passo 1: Preparar o diretório da instância `jamoto`

```bash
# Vá para a raiz do seu servidor web onde ficam os projetos
cd /var/www/

# Crie a pasta do projeto jamoto e entre nela
mkdir jamoto_patrimonial
cd jamoto_patrimonial

# Inicie o repositório git e conecte-o ao seu repositório remoto
git init
git remote add origin URL_DO_SEU_REPOSITORIO.git

# Faça o pull da branch principal (ex: main)
git pull origin main
```

## Passo 2: Configurar o Ambiente Virtual e Dependências

```bash
# Crie e ative o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instale as bibliotecas vitais e dependências do projeto
pip install -U pip
pip install -r requirements.txt
```

> **Aviso Importante sobre o PostgreSQL e o .env**
> 
> Você precisa criar o banco `jamoto_db` e o usuário `jamoto_user`.
> 
> 1. No servidor, abra o terminal do PostgreSQL:
> ```bash
> sudo -u postgres psql
> ```
> 
> 2. Cole os seguintes comandos e insira uma senha forte onde estiver `SUA_SENHA_AQUI`:
> ```sql
> CREATE DATABASE jamoto_db;
> CREATE USER jamoto_user WITH PASSWORD '*Marien2012';
> ALTER ROLE jamoto_user SET client_encoding TO 'utf8';
> ALTER ROLE jamoto_user SET default_transaction_isolation TO 'read committed';
> ALTER ROLE jamoto_user SET timezone TO 'America/Sao_Paulo';
> GRANT ALL PRIVILEGES ON DATABASE jamoto_db TO jamoto_user;
> \c jamoto_db
> GRANT ALL ON SCHEMA public TO jamoto_user;
> \q
> ```
> 
> 3. De volta à pasta `/var/www/jamoto_patrimonial`, crie o `.env`:
> ```bash
> nano .env
> ```
> 
> 4. Preencha com as suas definições básicas de ambiente:
> ```ini
> DEBUG=False
> SECRET_KEY=COLOQUE_UMA_CHAVE_SECRETA_AQUI
> DATABASE_URL=postgres://jamoto_user:SUA_SENHA_AQUI@127.0.0.1:5432/jamoto_db
> ```

## Passo 3: Frontend, Migrações e Estáticos

Você usou Vite (Tailwind), então vamos rodar o build do front-end e coletar.

```bash
npm install
npm run build

# Executar as migrações no banco que acabamos de criar
python manage.py migrate

# Copiar os arquivos estáticos para o local correto
python manage.py collectstatic --noinput

# Crie seu usuário administrador
python manage.py createsuperuser
```

Em seguida, garanta que o web server terá permissão de leitura nos arquivos:
```bash
cd /var/www/
chown -R www-data:www-data jamoto_patrimonial
```

## Passo 4: Ativando os Serviços Gunicorn e Nginx

Conecte as configurações que subimos no git com os diretórios-chave do Linux:

```bash
# Registrar, habilitar e subir o Gunicorn (`jamoto` na porta 8013)
ln -s /var/www/jamoto_patrimonial/gunicorn_jamoto.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable gunicorn_jamoto
systemctl start gunicorn_jamoto

# Verifique se está tudo verdinho
systemctl status gunicorn_jamoto

# Registrar o arquivo do Nginx e vinculá-lo
ln -s /var/www/jamoto_patrimonial/nginx_jamoto.conf /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/nginx_jamoto.conf /etc/nginx/sites-enabled/

# Testar se a sintaxe está ok e reiniciar Nginx
nginx -t
systemctl restart nginx
```

## Passo 5: Certificado de Segurança SSL (Via Certbot)

Por fim, rode o certbot para emitir o cadeadinho HTTPs grátis para `jamoto.gestorpatrimonial.com.br`:

```bash
certbot --nginx -d jamoto.gestorpatrimonial.com.br
```

---

Lembre-se apenas que o domínio `jamoto.gestorpatrimonial.com.br` já precisa estar apontado para o mesmo servidor antes de rodar o comando do certbot. Pronto! A instância estará no ar de forma isolada!
