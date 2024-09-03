![](static/cover.png)

#### ДигиТекс је вишеплатформна апликација за дигитализацију докумената на српском језику, заснована на оптичком препознавању карактера (и језичким моделима*).

#### Документ који је предмет дигитализације се најпре трансформише у слику помоћу [Поплера](https://poppler.freedesktop.org/), док је за препознавање текста на слици задужен [Гугл Тесеракт](https://github.com/tesseract-ocr/tesseract). (Коначно, текст се обрађује језичким моделом за српски језик, [јертех355](https://huggingface.co/jerteh/Jerteh-355), што омогућава прецизније одређивање вероватноће сваке речи у контексту, као и аутоматско исправљање лоше рашчитаног текста.*) 

#### Дигитекс се може покретати као [Фласк](https://flask.palletsprojects.com/) веб апликација на рачунарима са _Виндоус_ и _Виндоус сервер_ оперативним системима, за шта је неопходно инсталирати [Пајтон 3.12](https://www.python.org/downloads/release/python-3120/), или се може скинути и покренути компајлована верзија која у себи садржи неопходан софтвер.

# Покретање апликације

## Виндоус апликација

Скините прекомпајловану апликацију доступну на [Гитхаб репозиторијуму софтвера](https://github.com/procesaur/digiteks/releases) и покрените програм на вашем рачунару.

## Виндоус (командна линија, припремљено виртуелно окружење)
1. Преузмите апликацију у целости и сачувајте је на вашем рачунару.

2. Инсталирајте Пајтон интерпретер (препоручена верзија 3.12)

3. У командној линији подесите радно окружење на директоријум у којем је похрањен преузети софтвер
```console
cd ./direktorijum/digiteks/softvera
```

4. Покрените припремљено виртуелно окружење
```console
.\venv\Scripts\activate
```

5. Покрените апликацију
```console
python main.py
```

## Виндоус (командна линија, ваше Пајтон окружење)
1. Преузмите апликацију у целости и сачувајте је на вашем рачунару.

2. Инсталирајте Пајтон интерпретер (препоручена верзија 3.12) 

3. У командној линији подесите радно окружење на директоријум у којем је похрањен преузети софтвер
```console
cd ./direktorijum/digiteks/softvera
```

4. Инсталиратје неопходне Пајтон пакете
```console
pip install -r requirements.txt
```

5. Преузмите инсталацију пакета _tesserocr_ за вашу верзију Пајтон интерпретера на [овој адреси](https://github.com/simonflueckiger/tesserocr-windows_build/releases)

6. Инсталирајте преузети пакет (_tesserocr_) 
```console
pip install <путања/преузетог/пакета/име>.whl
```

5. Покрените апликацију
```console
python main.py
```

## Linux (командна линија, ваше Пајтон окружење)
1. Преузмите апликацију у целости и сачувајте је на вашем рачунару.

2. Инсталирајте Пајтон интерпретер (препоручена верзија 3.12) 

3. У командној линији подесите радно окружење на директоријум у којем је похрањен преузети софтвер
```console
cd ./direktorijum/digiteks/softvera
```

4. Инсталиратје неопходне Пајтон пакете
```console
pip install -r requirements.txt
```

5. Инсталирајте _Tesseract_
```console
sudo apt-get install tesseract-ocr libtesseract-dev libleptonica-dev pkg-config
```

6. Инсталирајте _Poppler_
```console
sudo apt-get install -y poppler-utils
```

7. Инсталирајте пакет (_tesserocr_) 
```console
pip install tesserocr
```

8. Покрените апликацију
```console
python main.py
```

## _apache_ веб апликација (_Linux_ пример)
1. Преузмите апликацију у целости и сачувајте је на вашем рачунару (нпр. у директоријуму _var/www/digiteks_).

2. Инсталирајте Пајтон интерпретер (препоручена верзија 3.12) 

3. У командној линији подесите радно окружење на директоријум у којем је похрањен преузети софтвер
```console
cd ./direktorijum/digiteks/softvera
```

4. Инсталиратје неопходне Пајтон пакете
```console
sudo -H pip3 install -r requirements.txt
```

5. Инсталирајте _Tesseract_
```console
sudo apt-get install tesseract-ocr libtesseract-dev libleptonica-dev pkg-config ffmpeg libsm6 libxext6
```

6. Инсталирајте _Poppler_
```console
sudo apt-get install -y poppler-utils
```

7. Инсталирајте пакет (_tesserocr_) 
```console
sudo -H pip3 install tesserocr
```

8. Инсталација и подешавање _apache_ веб сервера

```console
sudo apt install apache2
apache2 -v
sudo apt-get install libapache2-mod-wsgi-py3
sudo a2enmod rewrite
sudo a2enmod wsgi
sudo nano /etc/apache2/sites-available/digiteks.conf
```

У конфигурациону датотеку упишите:

```apache
<VirtualHost *:5001>

WSGIDaemonProcess digiteks user=www-data group=www-data threads=5
        WSGIScriptAlias / /var/www/digiteks/digiteks.wsgi

        <Directory /var/www/digiteks>
                WSGIProcessGroup digiteks
                WSGIApplicationGroup %{GLOBAL}
                Order deny,allow
                Allow from 127.0.0.1 ::1/128 <ADRESA SERVERA>
        </Directory>
</VirtualHost>

```

sudo nano /etc/apache2/ports.conf
```apache
Listen 5001
```

Урадите неопходно ажурирање и рестарт сервиса

```console
sudo a2ensite digiteks
sudo service apache2 restart
```

и апликација ће бити покренута и доступна на порту 5001

# Предстојећи кораци:
1. Припремање прекомпајловане апликације за _Linux_ оперативне системе;

2. Припрема детаљнијег упутства за употребу;

2. Имплементација адекватних језичких модела путем библиотеке _трансформерс_.

# Напомене

#### Развој апликације, у сарадњи са *ЈП Службени Гласник*, омогућио је програм *Говтех*, који финансира *Фонд за иновациону делатност Републике Србије*.


#### *Функционланости још увек нису имплементиране.