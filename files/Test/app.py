import locale
from logging import FileHandler, Formatter
import os
import platform
import subprocess
import sys

from flask import Flask, session, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from passlib.hash import pbkdf2_sha256
from wtforms import PasswordField, validators

APP_SECRET_KEY = 'O\xf2D\xcf""\xa2\xa9\x00\xca\xf9o\x80\x04\xffO\x9c5Yt\xf5Nw\x82'
PASSWORD_HASH = '$pbkdf2-sha256$29000$QOh9r1UKYczZu5eSspYS4g$igyd/96mvcGbtnwB9yofjVthr4.VC7z.YXu404dR1g8'

app = Flask(__name__)
app.secret_key = APP_SECRET_KEY


class AuthForm(FlaskForm):
    password = PasswordField('Password', [validators.InputRequired()])

class LockForm(FlaskForm):
    pass


@app.route('/login', methods=['POST'])
def login():
    auth_form = AuthForm(request.form)

    if auth_form.validate():
        if pbkdf2_sha256.verify(auth_form.password.data, PASSWORD_HASH):
            session['logged_in'] = True
        else:
            if 'logged_in' in session:
                session.pop('logged_in')
                
    return redirect(url_for('test'))


@app.route('/logout', methods=['POST'])
def logout():
    lock_form = LockForm(request.form)

    if lock_form.validate():
        if 'logged_in' in session:
            session.pop('logged_in')
            
    return redirect(url_for('test'))


@app.route('/')
def test():
    auth_form = AuthForm()
    lock_form = LockForm()
    
    if not session.get('logged_in'):
        return render_template('form.html', form=auth_form)
    else:
        data = ''
        try:
            import psutil
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            disk = psutil.disk_usage('/')
            mem_divisor, mem_units, mem_formatting = (1024**2, 'MB', '.0f') if mem.used // 1024**3 < 1 else (1024**3, 'GB', '.1f')
            data += 'Uptime: {}'.format(subprocess.check_output(['uptime', '-p']).strip().decode('ascii')[3:])
            data += '<br>CPU ({} cores): {}%'.format(psutil.cpu_count(), psutil.cpu_percent(interval=0.5))
            data += '<br>Load avg: {} {} {}'.format(*os.getloadavg())
            data += '<br>Memory: {{:{0}}} / {{:{0}}} {{}}'.format(mem_formatting).format(mem.used / mem_divisor, mem.total / mem_divisor, mem_units)
            data += '<br>Swap: {{:{0}}} / {{:{0}}} {{}}'.format(mem_formatting).format(swap.used / mem_divisor, swap.total / mem_divisor, mem_units)
            data += '<br>Disk: {:.1f} / {:.1f} GB'.format(disk.used / 1024**3, disk.total / 1024**3)
        except ImportError:
            data += '<br>psutil not available' 
        
        data += '<br><br>OS: {} ({})'.format(platform.platform(), platform.machine()) 
        data += '<br>Python: {} ({})'.format(sys.version, platform.architecture()[0])
        data += '<br>PWD: {}'.format(os.getcwd())   
        
        data += '<br><br>Locale: ' + str(locale.getlocale())
        data += '<br>Filename encoding: ' + sys.getfilesystemencoding()     

        try:
            import pip
            packages = pip.get_installed_distributions(local_only=True)
            data += '<br><br>PIP packages:<br>' + '<br>'.join(sorted(['{} ({})'.format(a.project_name, a.version) for a in packages], key=str.lower))
        except:
            data += '<br><br>PIP not working'        

        try:
            import sqlite3
            data += '<br><br>sqlite3: {}'.format(sqlite3.version)
        except ImportError:
            data += '<br><br>sqlite3 not available'     
            
        benchmark = os.path.join(os.getcwd(), 'data', 'benchmark.log')
        if os.path.exists(benchmark):
            data += '<br><br><pre>'
            data += open(benchmark).read()
            data += '</pre>'            

        return render_template('values.html', data=data, form=lock_form)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
else:
    handler = FileHandler('data/app.log')
    handler.setFormatter(Formatter('[%(asctime)s | %(levelname)s] %(message)s'))
    app.logger.addHandler(handler)
