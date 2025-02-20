# DjangoRabbitMQ_Celery
Se realizará una aplicación básica de Django como publicador de una tarea, el broker será RabbitMQ y el suscriptor Celery

# Primero creamos el Dockerfile
    FROM python:3.13.2-alpine3.21

    ENV PYTHONUNBUFFERED=1

    WORKDIR /code

    COPY requirements.txt /code/

    RUN python -m pip install --upgrade pip && \
        pip install -r requirements.txt

    COPY . /code/
    RUN apk add --no-cache bash

    COPY wait-for-it.sh /code/wait-for-it.sh
    RUN chmod +x /code/wait-for-it.sh

# Luego el requirements.txt
    Django==4.2.9
    psycopg2-binary==2.9.10 
    pillow==11.1.0
    django-celery-beat
    celery>=5.0,<6.0

# Creamos el wait-for-it.sh
    #!/usr/bin/env bash
    # Use this script to test if a given TCP host/port are available

    WAITFORIT_cmdname=${0##*/}

    echoerr() { if [[ $WAITFORIT_QUIET -ne 1 ]]; then echo "$@" 1>&2; fi }

    usage()
    {
        cat << USAGE >&2
    Usage:
        $WAITFORIT_cmdname host:port [-s] [-t timeout] [-- command args]
        -h HOST | --host=HOST       Host or IP under test
        -p PORT | --port=PORT       TCP port under test
                                    Alternatively, you specify the host and port as host:port
        -s | --strict               Only execute subcommand if the test succeeds
        -q | --quiet                Don't output any status messages
        -t TIMEOUT | --timeout=TIMEOUT
                                    Timeout in seconds, zero for no timeout
        -- COMMAND ARGS             Execute command with args after the test finishes
    USAGE
        exit 1
    }

    wait_for()
    {
        if [[ $WAITFORIT_TIMEOUT -gt 0 ]]; then
            echoerr "$WAITFORIT_cmdname: waiting $WAITFORIT_TIMEOUT seconds for $WAITFORIT_HOST:$WAITFORIT_PORT"
        else
            echoerr "$WAITFORIT_cmdname: waiting for $WAITFORIT_HOST:$WAITFORIT_PORT without a timeout"
        fi
        WAITFORIT_start_ts=$(date +%s)
        while :
        do
            if [[ $WAITFORIT_ISBUSY -eq 1 ]]; then
                nc -z $WAITFORIT_HOST $WAITFORIT_PORT
                WAITFORIT_result=$?
            else
                (echo -n > /dev/tcp/$WAITFORIT_HOST/$WAITFORIT_PORT) >/dev/null 2>&1
                WAITFORIT_result=$?
            fi
            if [[ $WAITFORIT_result -eq 0 ]]; then
                WAITFORIT_end_ts=$(date +%s)
                echoerr "$WAITFORIT_cmdname: $WAITFORIT_HOST:$WAITFORIT_PORT is available after $((WAITFORIT_end_ts - WAITFORIT_start_ts)) seconds"
                break
            fi
            sleep 1
        done
        return $WAITFORIT_result
    }

    wait_for_wrapper()
    {
        # In order to support SIGINT during timeout: http://unix.stackexchange.com/a/57692
        if [[ $WAITFORIT_QUIET -eq 1 ]]; then
            timeout $WAITFORIT_BUSYTIMEFLAG $WAITFORIT_TIMEOUT $0 --quiet --child --host=$WAITFORIT_HOST --port=$WAITFORIT_PORT --timeout=$WAITFORIT_TIMEOUT &
        else
            timeout $WAITFORIT_BUSYTIMEFLAG $WAITFORIT_TIMEOUT $0 --child --host=$WAITFORIT_HOST --port=$WAITFORIT_PORT --timeout=$WAITFORIT_TIMEOUT &
        fi
        WAITFORIT_PID=$!
        trap "kill -INT -$WAITFORIT_PID" INT
        wait $WAITFORIT_PID
        WAITFORIT_RESULT=$?
        if [[ $WAITFORIT_RESULT -ne 0 ]]; then
            echoerr "$WAITFORIT_cmdname: timeout occurred after waiting $WAITFORIT_TIMEOUT seconds for $WAITFORIT_HOST:$WAITFORIT_PORT"
        fi
        return $WAITFORIT_RESULT
    }

    # process arguments
    while [[ $# -gt 0 ]]
    do
        case "$1" in
            *:* )
            WAITFORIT_hostport=(${1//:/ })
            WAITFORIT_HOST=${WAITFORIT_hostport[0]}
            WAITFORIT_PORT=${WAITFORIT_hostport[1]}
            shift 1
            ;;
            --child)
            WAITFORIT_CHILD=1
            shift 1
            ;;
            -q | --quiet)
            WAITFORIT_QUIET=1
            shift 1
            ;;
            -s | --strict)
            WAITFORIT_STRICT=1
            shift 1
            ;;
            -h)
            WAITFORIT_HOST="$2"
            if [[ $WAITFORIT_HOST == "" ]]; then break; fi
            shift 2
            ;;
            --host=*)
            WAITFORIT_HOST="${1#*=}"
            shift 1
            ;;
            -p)
            WAITFORIT_PORT="$2"
            if [[ $WAITFORIT_PORT == "" ]]; then break; fi
            shift 2
            ;;
            --port=*)
            WAITFORIT_PORT="${1#*=}"
            shift 1
            ;;
            -t)
            WAITFORIT_TIMEOUT="$2"
            if [[ $WAITFORIT_TIMEOUT == "" ]]; then break; fi
            shift 2
            ;;
            --timeout=*)
            WAITFORIT_TIMEOUT="${1#*=}"
            shift 1
            ;;
            --)
            shift
            WAITFORIT_CLI=("$@")
            break
            ;;
            --help)
            usage
            ;;
            *)
            echoerr "Unknown argument: $1"
            usage
            ;;
        esac
    done

    if [[ "$WAITFORIT_HOST" == "" || "$WAITFORIT_PORT" == "" ]]; then
        echoerr "Error: you need to provide a host and port to test."
        usage
    fi

    WAITFORIT_TIMEOUT=${WAITFORIT_TIMEOUT:-15}
    WAITFORIT_STRICT=${WAITFORIT_STRICT:-0}
    WAITFORIT_CHILD=${WAITFORIT_CHILD:-0}
    WAITFORIT_QUIET=${WAITFORIT_QUIET:-0}

    # Check to see if timeout is from busybox?
    WAITFORIT_TIMEOUT_PATH=$(type -p timeout)
    WAITFORIT_TIMEOUT_PATH=$(realpath $WAITFORIT_TIMEOUT_PATH 2>/dev/null || readlink -f $WAITFORIT_TIMEOUT_PATH)

    WAITFORIT_BUSYTIMEFLAG=""
    if [[ $WAITFORIT_TIMEOUT_PATH =~ "busybox" ]]; then
        WAITFORIT_ISBUSY=1
        # Check if busybox timeout uses -t flag
        # (recent Alpine versions don't support -t anymore)
        if timeout &>/dev/stdout | grep -q -e '-t '; then
            WAITFORIT_BUSYTIMEFLAG="-t"
        fi
    else
        WAITFORIT_ISBUSY=0
    fi

    if [[ $WAITFORIT_CHILD -gt 0 ]]; then
        wait_for
        WAITFORIT_RESULT=$?
        exit $WAITFORIT_RESULT
    else
        if [[ $WAITFORIT_TIMEOUT -gt 0 ]]; then
            wait_for_wrapper
            WAITFORIT_RESULT=$?
        else
            wait_for
            WAITFORIT_RESULT=$?
        fi
    fi

    if [[ $WAITFORIT_CLI != "" ]]; then
        if [[ $WAITFORIT_RESULT -ne 0 && $WAITFORIT_STRICT -eq 1 ]]; then
            echoerr "$WAITFORIT_cmdname: strict mode, refusing to execute subprocess"
            exit $WAITFORIT_RESULT
        fi
        exec "${WAITFORIT_CLI[@]}"
    else
        exit $WAITFORIT_RESULT
    fi   

# Ahora con ello creamos el docker-compose.yml
    
    services:
    
    db:
        image: postgres:15.10
        restart: always 
        container_name: postgresql
                
        volumes:
        - ./data/db:/var/lib/postgresql/data
        environment: 
        - DATABASE_HOST=127.0.0.1
        - POSTGRES_DB=my_database
        - POSTGRES_USER=admin
        - POSTGRES_PASSWORD=admin
        ports:
        - "5432:5432"
            
    pgadmin:
        image: dpage/pgadmin4
        container_name: pgadmin
        environment:
        - PGADMIN_DEFAULT_EMAIL=jamer.omar.asencio.urcia@gmail.com
        - PGADMIN_DEFAULT_PASSWORD=admin
        ports:
        - "5050:5050"
        depends_on:
        - db
    

            
    web:
        build: .
        container_name: django
        command: python manage.py runserver 0.0.0.0:8000
        volumes:
        - .:/code
        ports:
        - "8000:8000"
        environment:
        - POSTGRES_NAME=my_database
        - POSTGRES_USER=admin
        - POSTGRES_PASSWORD=admin
        depends_on:
        - db
        - rabbitmq
    
    rabbitmq:
        image: rabbitmq:3-management
        container_name: rabbitmq
        ports:
        - "5672:5672" # Puerto AMQP
        - "15672:15672" # Interfaz de administración
        environment:
        - RABBITMQ_ERLANG_COOKIE=some_secret_cookie
        restart: always
        healthcheck:
        test: ["CMD", "rabbitmq-diagnostics", "status"]
        interval: 10s
        timeout: 5s
        retries: 5
    
    celery:
        build: .
        container_name: celery_worker
        command: ["/code/wait-for-it.sh", "rabbitmq:5672", "--", "celery", "-A", "django_docker", "worker", "--loglevel=info"]
        volumes:
        - .:/code
        depends_on:
        - rabbitmq
        - db
        - web


# Ahora vamos a ejecutar:

    docker compose run web django-admin startproject django_docker .

 # En settings.py debemos de agregar lo de Celery
    # Configuración de Celery
    CELERY_BROKER_URL = 'amqp://guest:guest@rabbitmq:5672//'
    CELERY_RESULT_BACKEND = 'rpc://'

# Debemos crear además el archivo celery.py
    import os
    from celery import Celery

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_docker.settings')

    app = Celery('django_docker')

    # Usar string para evitar que se serialice la configuración
    app.config_from_object('django.conf:settings', namespace='CELERY')

    # Autodiscover tasks de las apps de Django
    app.autodiscover_tasks()

# Nota: en Celery.py en la parte:
    django_docker es el nombre de tu project django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_docker.settings')

# Ahora en el project de django en settings.py:

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'myapp',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'my_database',
        'USER': 'admin',
        'PASSWORD': 'admin',
        'HOST': 'db',
        'PORT': 5432
    }
}

# Ahora creamos una app en django la cual se llamrá: myapp
    docker exec django python manage.py startapp myapp

# AHORA COMO HACEMOS CON LAS MIGRACIONES PARA NUESTRO PROYECTO DJANGO?
    Abro otra terminal y ejecuto:
        docker compose run web python manage.py makemigrations
        docker compose run web python manage.py migrate

# AHORA PARA CREAR EL SUPERUSUARIO:
      
      docker exec -it django python manage.py createsuperuser

  it: para que sea una pantalla iterativa

# Para finalizar creamos en myapp:
    tasks.py:
        # myapp/tasks.py
        from celery import shared_task

        @shared_task
        def send_welcome_email(email):
            # Aquí simulas el envío de un correo, en un caso real usarías una función para enviar email.
            print(f"Welcome email sent to {email}")
            return f"Email sent to {email}"

    urls.py:
        # myapp/urls.py
        from django.urls import path
        from .views import register_many

        urlpatterns = [
            path("register-many/", register_many, name="register_many"),
        ]
    
    views.py:
        # myapp/views.py
        from django.http import HttpResponse
        from .tasks import send_welcome_email

        def register_many(request):
            email = "user@example.com"
            task_ids = []
            # Encola 50 tareas
            for i in range(150):
                result = send_welcome_email.delay(f"{i}-{email}")
                task_ids.append(result.id)
            return HttpResponse(f"Se han encolado 50 tareas: {task_ids}")

    
    en __init__.py:
        # myapp/__init__.py
        from . import tasks


# En el proyecto django-docker:
    __init__.py:
        # project/__init__.py
        from .celery import app as celery_app

        __all__ = ("celery_app",)
    
    celery.py:
        import os
        from celery import Celery

        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_docker.settings')

        app = Celery('django_docker')

        # Usar string para evitar que se serialice la configuración
        app.config_from_object('django.conf:settings', namespace='CELERY')

        # Autodiscover tasks de las apps de Django
        app.autodiscover_tasks()


    en urls.py:
        from django.contrib import admin
        from django.urls import path,include

        urlpatterns = [
            path('admin/', admin.site.urls),
            path('myapp/', include('myapp.urls')),
        ]

