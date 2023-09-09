## Проект **Foodgram** - это социальная сеть для обмена рецептами.
Ссылка на сайт без https, только http:
[foodgram](http://fedorthedross.ddnsking.com/)

логин админа:
admin@admin.admin
пароль:
admin

## Описание

Реализована возможность регистрации пользователей, добавления, удаления и изменения информации о рецептах.

Есть возможность скачать список для покупок на основе корзины с рецептами.

Есть возможность подписаться на автора интересных рецептов.

Проект может быть развернут на сервере с использованием Docker.

### Автор проекта: [Федор](https://github.com/thedross)
### Список использованных технологий при разработке: 


`Python` 

`Django`

`djangorestframework`

`Gunicorn` 

`Nginx`

`Docker`

`DockerCompose`

`React`

### Как запустить проект:

Установить docker на сервер.
Создать папку foodgram
клонировать nginx.conf в папку 
Клонировать docker-compose.yml туда же.
Создать файл .env и запустить сборку контейнеров:

```
git clone https://github.com/thedross/foodgram-project-react
```

```

```

Необходимая настройка .env :
Создать и разместить в .env в корневой директории проекта переменные:
SECRET_KEY = <ключ доступа к серверу>
Также необходимо добавить в secrets на гитхаб несколько переменных.

# Foodgram
[![foodgram_workflow](https://github.com/thedross/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)](https://github.com/thedross/foodgram-project-react/actions/workflows/foodgram_workflow.yml)

## Инструкция для запуска на удаленном сервере

#### Secrets для CI/CD
```
# В Settings - Secrets and variables - Actions 
добавьте secrets c вашими данными

DOCKER_USERNAME
DOCKER_PASSWORD
HOST
USER
SSH_KEY
PASSPHRASE
```
#### Покдлючитесь к серверу
```
ssh username@server_ip
```

Пример файла .env
```
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

