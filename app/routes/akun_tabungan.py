from flask import Blueprint, render_template, redirect, request, url_for, session
from functools import wraps
from app import supabase
from datetime import date

akun_tabungan_bp = Blueprint('akun_tabungan', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.auth'))
        return f(*args, **kwargs)
    return decorated_function

@akun_tabungan_bp.route('/daftar_akun_tabungan', methods=['GET'])
@login_required
def akun_tabungan():
    response = supabase.table('akun_tabungan').select('total').execute()
    total_saldo = 0
    if response.data:
        for akun in response.data:
            total_saldo += float(akun['total'])
        total_saldo = f"Rp {total_saldo:,.2f}"
    else:
        total_saldo = "Belum ada akun tabungan yang terdaftar"

    tab = request.args.get('tab', '')
    message = request.args.get('message', '')

    edit_akun = None
    edit_akun_id = request.args.get('edit_akun_id')
    if edit_akun_id:
        response = supabase.table('akun_tabungan').select('*').eq('id', edit_akun_id).execute()
        if response.data:
            edit_akun = response.data[0]

    transfer_akun = None
    transfer_akun_id = request.args.get('transfer_akun_id')
    if transfer_akun_id:
        response = supabase.table('akun_tabungan').select('*').eq('id', transfer_akun_id).execute()
        if response.data:
            transfer_akun = response.data[0]

    response = supabase.table('akun_tabungan').select('*').order('nama_akun', desc=False).execute()
    data_akun_tabungan = response.data

    return render_template('akun_tabungan.html', total_saldo=total_saldo, data_akun_tabungan=data_akun_tabungan, tab=tab, message=message, edit_akun=edit_akun, transfer_akun=transfer_akun)

@akun_tabungan_bp.route('/tambah_akun', methods=['GET', 'POST'])
@login_required
def tambah_akun():
    input_nama_akun = request.form.get('input_nama_akun')
    input_total = request.form.get('input_total')

    nama_akun = input_nama_akun.capitalize()
    total = float(input_total)

    response = supabase.table('akun_tabungan').select('*').eq('nama_akun', nama_akun).execute()

    if response.data and len(response.data) > 0:
        return redirect(url_for('akun_tabungan.akun_tabungan', tab="tambah_akun", message="Akun yang sama sudah ada, silahkan buat yang baru"))

    if input_nama_akun and input_total:
        supabase.table('akun_tabungan')\
            .insert({
                "nama_akun": nama_akun,
                "total": total
            }).execute()
        return redirect(url_for('akun_tabungan.akun_tabungan', tab='', message=''))        

@akun_tabungan_bp.route('/edit_akun/<id>', methods=['GET', 'POST'])
@login_required
def edit_form(id):
    return redirect(url_for('akun_tabungan.akun_tabungan', edit_akun_id=id))

@akun_tabungan_bp.route('/update_akun/<id>', methods=['POST'])
@login_required
def update(id):
    input_nama_akun_baru = request.form.get('input_nama_akun_baru')
    input_total_akun_baru = request.form.get('input_total_akun_baru')

    response = supabase.table('akun_tabungan').select('*').eq('nama_akun', input_nama_akun_baru).neq('id', id).execute()

    if response.data:
        return redirect(url_for('akun_tabungan.akun_tabungan', edit_akun=id, tab='edit_akun', message='Sudah ada nama akun tabungan yang sama, gunakan nama lain'))
    
    supabase.table('akun_tabungan')\
        .update({
            "nama_akun": input_nama_akun_baru,
            "total": input_total_akun_baru
        }).eq('id', id).execute()
    
    session.pop('edit_akun_data', None)
    session.pop('edit_akun_id', None)

    return redirect(url_for('akun_tabungan.akun_tabungan', tab='', message=''))

@akun_tabungan_bp.route('/transfer_akun_form/<id>', methods=['GET', 'POST'])
@login_required
def transfer_form(id):
    return redirect(url_for('akun_tabungan.akun_tabungan', transfer_akun_id=id))

@akun_tabungan_bp.route('/transfer_akun/<id>', methods=['GET', 'POST'])
@login_required
def transfer(id):
    target_transfer = request.form.get('target_transfer')
    input_total_transfer = request.form.get('input_total_transfer')
    total_transfer = float(input_total_transfer)

    response = supabase.table('akun_tabungan').select('*').eq('id', id).execute()
    data_sumber = response.data[0]
    total_sumber = float(data_sumber['total'])
    sumber_akhir = total_sumber - total_transfer

    response = supabase.table('akun_tabungan').select('*').eq('nama_akun', target_transfer).execute()
    data_target = response.data[0]
    total_target = float(data_target['total'])
    target_akhir = total_target + total_transfer

    supabase.table('akun_tabungan')\
        .update({
            'nama_akun': data_sumber['nama_akun'],
            'total': sumber_akhir
        }).eq('id', id).execute()
    supabase.table('akun_tabungan')\
        .update({
            'total': target_akhir
        }).eq('nama_akun', target_transfer).execute()

    session.pop('transfer_akun_data', None)
    session.pop('transfer_akun_id', None)

    return redirect(url_for('akun_tabungan.akun_tabungan', tab='', message=''))

@akun_tabungan_bp.route('/hapus_akun/<id>', methods=['POST'])
@login_required
def delete(id):
    response = supabase.table('akun_tabungan').select('*').eq('id', id).execute()
    data = response.data[0]
    nama_akun = data['nama_akun']

    supabase.table('data_historis').delete().eq('nama_akun', nama_akun).execute()
    supabase.table('akun_tabungan').delete().eq('id', id).execute()

    return redirect(url_for('akun_tabungan.akun_tabungan', tab='', message=''))