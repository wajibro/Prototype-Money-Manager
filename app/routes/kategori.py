from flask import Blueprint, render_template, redirect, request, url_for, session
from functools import wraps
from app import supabase

kategori_bp = Blueprint('kategori', __name__) 

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

@kategori_bp.route('/kategori', methods=['GET'])
@login_required
def kategori():
    tab_aktif = request.args.get('tab', 'pengeluaran')
    message = request.args.get('message', '')

    total_saldo_query = select_table(table='akun_tabungan', select='total')
    total_saldo = 0
    if total_saldo_query:
        for akun in total_saldo_query:
            total_saldo += float(akun['total'])
        total_saldo = f"Rp {total_saldo:,.2f}"
    else:
        total_saldo = "Belum ada akun tabungan yang terdaftar"

    total_pengeluaran_query = select_table(table='data_historis', select='total_perubahan', eq_col='jenis', eq_row='Pengeluaran')
    total_pengeluaran = 0
    if total_pengeluaran_query:
        for akun in total_pengeluaran_query:
            total_pengeluaran += float(akun['total_perubahan'])
        total_pengeluaran = f"Rp {total_pengeluaran:,.2f}"
    else:
        total_pengeluaran = 0

    total_pemasukan_query = select_table(table='data_historis', select='total_perubahan', eq_col='jenis', eq_row='Pemasukan')
    total_pemasukan = 0
    if total_pemasukan_query:
        for akun in total_pemasukan_query:
            total_pemasukan += float(akun['total_perubahan'])
        total_pemasukan = f"Rp {total_pemasukan:,.2f}"
    else:
        total_pemasukan = 0

    kategori = select_table(table='kategori', order_1='id', desc_1=False)

    akun_tabungan = select_table(table='akun_tabungan')

    return render_template(
        'kategori.html',
        total_saldo         = total_saldo,
        total_pengeluaran   = total_pengeluaran,
        total_pemasukan     = total_pemasukan,
        kategori            = kategori,
        akun_tabungan       = akun_tabungan,
        tab_aktif           = tab_aktif, message=message
    )

@kategori_bp.route('/simpan_pengeluaran', methods=['GET', 'POST'])
@login_required
def simpan_pengeluaran():
    input_tanggal                 = request.form.get('input_tanggal')
    input_kategori                = request.form.get('input_kategori')
    input_akun_tabungan           = request.form.get('input_akun_tabungan')
    input_total_perubahan         = request.form.get('input_total_perubahan')
    input_sub_kategori            = request.form.get('input_sub_kategori')

    total_perubahan = float(input_total_perubahan)
    total_tabungan = float(
        select_table(table='akun_tabungan', select='total', eq_col='nama_akun', eq_row=input_akun_tabungan)[0]['total']
    )

    total_akhir = total_tabungan - total_perubahan

    if input_kategori and input_akun_tabungan and input_total_perubahan:
        if input_sub_kategori == '':
            input_sub_kategori = "-"

        insert_table(
            table='data_historis',
            data={
                "tanggal"           : input_tanggal,
                "nama_akun"         : input_akun_tabungan,
                "jenis"             : "Pengeluaran",
                "kategori"          : input_kategori,
                "sub_kategori"      : input_sub_kategori,
                "total_perubahan"   : -total_perubahan,
                "total_akhir"       : total_akhir
            }
        )
        update_table(
            table='akun_tabungan',
            data={'total': total_akhir},
            eq_col='nama_akun', eq_row=input_akun_tabungan
        )

        return redirect(url_for('kategori.kategori', tab='pengeluaran'))

@kategori_bp.route('/simpan_pemasukan', methods=['GET', 'POST'])
@login_required
def simpan_pemasukan():
    input_tanggal                 = request.form.get('input_tanggal')
    input_kategori                = request.form.get('input_kategori')
    input_akun_tabungan           = request.form.get('input_akun_tabungan')
    input_total_perubahan         = request.form.get('input_total_perubahan')
    input_sub_kategori            = request.form.get('input_sub_kategori')

    sub_kategori = input_sub_kategori.capitalize()

    total_perubahan = float(input_total_perubahan)
    total_tabungan = float(
        select_table(table='akun_tabungan', select='total', eq_col='nama_akun', eq_row=input_akun_tabungan)[0]['total']
    )

    total_akhir = total_tabungan + total_perubahan

    if input_kategori and input_akun_tabungan and input_total_perubahan:
        if input_sub_kategori == '':
            input_sub_kategori = '-'

        insert_table(
            table='data_historis',
            data={
                "tanggal"           : input_tanggal,
                "nama_akun"         : input_akun_tabungan,
                "jenis"             : "Pemasukan",
                "kategori"          : input_kategori,
                "sub_kategori"      : sub_kategori,
                "total_perubahan"   : total_perubahan,
                "total_akhir"       : total_akhir
            }
        )
        update_table(
            table='akun_tabungan',
            data={'total': total_akhir},
            eq_col='nama_akun', eq_row=input_akun_tabungan
        )

    return redirect(url_for('kategori.kategori', tab='pemasukan'))

@kategori_bp.route('/tambah_kategori_pengeluaran', methods=['GET', 'POST'])
@login_required
def tambah_kategori_pengeluaran():
    input_kategori_baru = request.form.get('input_kategori_pengeluaran_baru')
    kategori_baru = input_kategori_baru.capitalize()

    data_query = select_table(table='kategori', eq_col='kategori', eq_row=kategori_baru)

    if data_query and len(data_query) > 0:
        return redirect(url_for('kategori.kategori', tab="tambah_kategori_pengeluaran", message="Kategori yang sama sudah ada, silahkan buat yang baru"))

    if input_kategori_baru:
        insert_table(
            table='kategori',
            data={
                "kategori"  : kategori_baru,
                "jenis"     : "Pengeluaran"
            }
        )
        return redirect(url_for('kategori.kategori', tab='pengeluaran'))

@kategori_bp.route('/tambah_kategori_pemasukan', methods=['GET', 'POST'])
@login_required
def tambah_kategori_pemasukan():
    input_kategori_baru = request.form.get('input_kategori_pemasukan_baru')

    kategori_baru = input_kategori_baru.capitalize()

    data_query = select_table(table='kategori', eq_col='kategori', eq_row=kategori_baru)

    if data_query and len(data_query) > 0:
        return redirect(url_for('kategori.kategori', tab="tambah_kategori_pemasukan", message="Kategori yang sama sudah ada, silahkan buat yang baru"))

    if input_kategori_baru:
        insert_table(
            table='kategori',
            data={
                "kategori"  : kategori_baru,
                "jenis"     : "Pemasukan"
            }
        )

        return redirect(url_for('kategori.kategori', tab='pemasukan'))