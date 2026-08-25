from flask import Blueprint, render_template, redirect, request, url_for, flash
from ..config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def auth():
    tab = request.args.get('tab', 'bisa')
    return render_template('auth.html', tab=tab)

@auth_bp.route('/login', methods=['POST'])
def login():
    input_pin = request.form.get('input_pin')

    pin = int(input_pin)
    correct_pin = int(Config.CORRECT_PIN)

    if pin == correct_pin:
        return redirect(url_for('kategori.kategori'))
    else:
        return render_template('auth.html', tab="gagal")