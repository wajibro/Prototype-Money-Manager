from flask import Blueprint, render_template, redirect, request, url_for, session
from functools import wraps
from app import supabase
from datetime import datetime

akun_tabungan_bp = Blueprint('akun_tabungan', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.auth'))
        return f(*args, **kwargs)
    return decorated_function

def select_table(table, select="*", eq_col=False, eq_row=False, neq_col=False, neq_row=False, order_1=False, desc_1=False, order_2=False, desc_2=False):
    query = supabase.table(table).select(select)
    if eq_col:
        query.eq(eq_col, eq_row)
    if neq_col:
        query.neq(neq_col, neq_row)
    if order_1:
        query.order(order_1, desc=desc_1)
    if order_2:
        query.order(order_2, desc=desc_2)
    response = query.execute()
    return response.data

def insert_table(table, data):
    supabase.table(table).insert(data).execute()

def update_table(table, data, eq_col, eq_row):
    supabase.table(table).update(data).eq(eq_col, eq_row).execute()

def delete_table(table, eq_col, eq_row):
    supabase.table(table).delete().eq(eq_col, eq_row).execute()

@akun_tabungan_bp.route('/daftar_akun_tabungan', methods=['GET'])
@login_required
def akun_tabungan():
    total_saldo_query = select_table(table='akun_tabungan', select='total')
    total_saldo = 0
    if total_saldo_query:
        for akun in total_saldo_query:
            total_saldo += float(akun['total'])
        total_saldo = f"Rp {total_saldo:,.2f}"
    else:
        total_saldo = "Belum ada akun tabungan yang terdaftar"

    bulan_ini = datetime.now().strftime("%Y-%m")
    total_pengeluaran_query = select_table(table='data_historis', eq_col='jenis', eq_row='Pengeluaran')
    total_pengeluaran = 0
    if total_pengeluaran_query:
        for akun in total_pengeluaran_query:
            if bulan_ini in akun['tanggal']:
                total_pengeluaran += float(akun['total_perubahan'])
        total_pengeluaran = f"Rp {total_pengeluaran:,.2f}"
    else:
        total_pengeluaran = 0

    total_pemasukan_query = select_table(table='data_historis', eq_col='jenis', eq_row='Pemasukan')
    total_pemasukan = 0
    if total_pemasukan_query:
        for akun in total_pemasukan_query:
            if bulan_ini in akun['tanggal']:
                total_pemasukan += float(akun['total_perubahan'])
        total_pemasukan = f"Rp {total_pemasukan:,.2f}"
    else:
        total_pemasukan = 0

    tab = request.args.get('tab', '')
    message = request.args.get('message', '')

    edit_akun = None
    edit_akun_id = request.args.get('edit_akun_id')
    if edit_akun_id:
        edit_akun_query = select_table(table='akun_tabungan', eq_col='id', eq_row=edit_akun_id)
        if edit_akun_query:
            edit_akun = edit_akun_query[0]

    transfer_akun = None
    transfer_akun_id = request.args.get('transfer_akun_id')
    if transfer_akun_id:
        transfer_akun_query = select_table(table='akun_tabungan', eq_col='id', eq_row=transfer_akun_id)
        if transfer_akun_query:
            transfer_akun = transfer_akun_query[0]

    data_akun_tabungan = select_table(table = 'akun_tabungan', order_1='nama_akun', desc_1=False)

    return render_template(
        'akun_tabungan.html',
        total_saldo         = total_saldo,
        total_pengeluaran   = total_pengeluaran,
        total_pemasukan     = total_pemasukan,
        data_akun_tabungan  = data_akun_tabungan,
        tab                 = tab,
        message             = message,
        edit_akun           = edit_akun,
        transfer_akun       = transfer_akun
    )

@akun_tabungan_bp.route('/tambah_akun', methods=['GET', 'POST'])
@login_required
def tambah_akun():
    input_nama_akun = request.form.get('input_nama_akun')
    input_total = request.form.get('input_total')

    nama_akun = input_nama_akun.capitalize()
    total = float(input_total)

    list_akun_query = select_table(table='akun_tabungan', eq_col='nama_akun', eq_row=nama_akun)

    if list_akun_query and len(list_akun_query) > 0:
        return redirect(url_for('akun_tabungan.akun_tabungan', tab="tambah_akun", message="Akun yang sama sudah ada, silahkan buat yang baru"))

    if input_nama_akun and input_total:
        data_akun_baru = {
            "nama_akun": nama_akun,
            "total": total
        }
        insert_table(table='akun_tabungan', data=data_akun_baru)
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

    nama_akun_query = select_table(table='akun_tabungan', eq_col='nama_akun', eq_row=input_nama_akun_baru, neq_col='id', neq_row=id)

    if nama_akun_query:
        return redirect(url_for('akun_tabungan.akun_tabungan', edit_akun=id, tab='edit_akun', message='Sudah ada nama akun tabungan yang sama, gunakan nama lain'))

    update_table(
        table='akun_tabungan',
        data={
            "nama_akun": input_nama_akun_baru,
            "total": input_total_akun_baru
        },
        eq_col='id', eq_row=id
    )

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

    data_sumber = select_table(table='akun_tabungan', eq_col='id', eq_row=id)[0]
    total_sumber = float(data_sumber['total'])
    sumber_akhir = total_sumber - total_transfer

    data_target = select_table(table='akun_tabungan', eq_col='nama_akun', eq_row=target_transfer)[0]
    total_target = float(data_target['total'])
    target_akhir = total_target + total_transfer

    update_table(
        table='akun_tabungan',
        data={
            'nama_akun': data_sumber['nama_akun'],
            'total': sumber_akhir
        },
        eq_col='id', eq_row=id
    )

    update_table(
        table='akun_tabungan',
        data={
            'total': target_akhir
        },
        eq_col='nama_akun', eq_row=target_transfer
    )

    session.pop('transfer_akun_data', None)
    session.pop('transfer_akun_id', None)

    return redirect(url_for('akun_tabungan.akun_tabungan', tab='', message=''))

@akun_tabungan_bp.route('/hapus_akun/<id>', methods=['POST'])
@login_required
def delete(id):
    data = select_table(table='akun_tabungan', eq_col='id', eq_row=id)[0]
    nama_akun = data['nama_akun']

    delete_table(table='data_historis', eq_col='nama_akun', eq_row=nama_akun)
    delete_table(table='akun_tabungan', eq_col='id', eq_row=id)

    return redirect(url_for('akun_tabungan.akun_tabungan', tab='', message=''))