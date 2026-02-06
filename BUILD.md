**Сборка**


Database
```
    sudo systemctl start postgresql && sudo systemctl enable postgresql
    sudo -u postgres psql
    CREATE DATABASE biblioteka_db;
    CREATE USER admin WITH PASSWORD 'admin';
    GRANT ALL PRIVILEGES ON DATABASE biblioteka_db TO admin;
    GRANT ALL PRIVILEGES ON SCHEMA public TO admin;
    ALTER ROLE admin SET search_path TO public;
    \q
```


Linux
```
    git clone https://github.com/osipenco/biblioteka
    cd biblioteka
    sudo apt install python3.12-venv && python3 -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    flask run
```


Docker
```
    sudo apt install docker.io
    sudo systemctl start docker && sudo systemctl enable docker
    sudo docker build -t biblioteka .
    sudo docker run -p 12345:12345 biblioteka
```


Docker-compose
```
    sudo apt install python3-setuptools docker-compose
    sudo docker-compose up
```
