from flask import Blueprint, render_template, redirect, request, url_for, session
from ..config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def auth():
    if session.get('logged_in'):
        return redirect(url_for('kategori.kategori'))

    tab = request.args.get('tab', 'bisa')
    return render_template('auth.html', tab=tab)

@auth_bp.route('/login', methods=['POST'])
def login():
    input_pin = request.form.get('input_pin')

    pin = int(input_pin)
    correct_pin = int(Config.CORRECT_PIN)

    if pin == correct_pin:
        session['logged_in'] = True
        session['pin_verified'] = True
        return redirect(url_for('kategori.kategori'))
    else:
        return render_template('auth.html', tab="gagal")

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('auth.auth'))