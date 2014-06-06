#!/bin/sh

PROJECT=wheelcms_axle
DJANGO_VERSION=Django==1.6.2
PYENV_HOME=$WORKSPACE/.pyenv/

# Delete previously built virtualenv
if [ -d $PYENV_HOME ]; then
    rm -rf $PYENV_HOME
fi

# Create virtualenv and install necessary packages
virtualenv --no-site-packages $PYENV_HOME
. $PYENV_HOME/bin/activate

pip install -q --use-mirrors $DJANGO_VERSION
pip install -q --use-mirrors -r requirements.txt
pip install -q coverage
pip install -q .

coverage run --source=$PROJECT ./quicktest.py --junit-xml $PROJECT-test.xml
coverage xml -o $PROJECT-coverage.xml
