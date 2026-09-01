from flask import Blueprint, render_template, redirect, request, url_for, session
from functools import wraps
from app import supabase
from datetime import date, datetime

histori_bp = Blueprint('histori', __name__)

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

@histori_bp.app_template_filter('format_tanggal')
def format_tgl_en_filter(date_str):
    if not date_str:
        return ""
    
    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%d, %b %Y')

@histori_bp.route('/histori', methods=['GET'])
@login_required
def histori():
    edit_histori = None
    edit_histori_id = request.args.get('edit_histori_id')
    if edit_histori_id:
        edit_data = select_table(table='data_historis', eq_col='id', eq_row=edit_histori_id)
        if edit_data:
            edit_histori = edit_data[0]

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

    data = select_table(table='data_historis')
    tanggal = sorted(list(set(p['tanggal'] for p in data)))
    tanggal.sort(reverse=True)

    data_sehari = []
    pengeluaran_sehari = []
    pemasukan_sehari = []
    cash_flow_sehari = []
    for p in tanggal:
        per_tanggal = select_table(table='data_historis', eq_col='tanggal', eq_row=p, order_1='id', desc_1=True)
        data_sehari.append(per_tanggal)

        total_pemasukan_sehari = 0
        total_pengeluaran_sehari = 0

        for p in per_tanggal:
            if p['jenis'] == 'Pemasukan':
                total_pemasukan_sehari += p['total_perubahan']
            elif p['jenis'] == 'Pengeluaran':
                total_pengeluaran_sehari += p['total_perubahan']

        cash_flow = total_pemasukan_sehari + total_pengeluaran_sehari
        cash_flow_sehari.append(f"{cash_flow:,.2f}")
        pengeluaran_sehari.append(f"{total_pengeluaran_sehari:,.2f}")
        pemasukan_sehari.append(f"{total_pemasukan_sehari:,.2f}")

    data_historis = zip(tanggal, pengeluaran_sehari, pemasukan_sehari, cash_flow_sehari, data_sehari)

    akun_tabungan = select_table(table='akun_tabungan', select='nama_akun')
    kategori = select_table('kategori', select='kategori')

    return render_template(
        'histori.html',
        total_saldo         = total_saldo,
        total_pengeluaran   = total_pengeluaran,
        total_pemasukan     = total_pemasukan,
        data_historis       = data_historis,
        edit_histori        = edit_histori,
        akun_tabungan       = akun_tabungan,
        kategori            = kategori
    )

@histori_bp.route('/edit_histori/<id>', methods=['GET', 'POST'])
@login_required
def edit_form(id):
    return redirect(url_for('histori.histori', edit_histori_id=id))

@histori_bp.route('/histori_update/<id>', methods=['GET', 'POST'])
@login_required
def update(id):
    input_nama_akun_baru    = request.form.get('input_nama_akun_baru')
    input_kategori_baru     = request.form.get('input_kategori_baru')
    input_sub_kategori_baru = request.form.get('input_sub_kategori_baru')
    input_perubahan_baru    = request.form.get('input_perubahan_baru')
    input_tanggal_baru      = request.form.get('input_tanggal_baru')
    perubahan_baru = float(input_perubahan_baru)

    data_lama = select_table(table='data_historis', eq_col='id', eq_row=id)[0]
    akun_tabungan_query = select_table(table='akun_tabungan', eq_col='nama_akun', eq_row=input_nama_akun_baru.capitalize())[0]
    akun_lama = data_lama['nama_akun']
    perubahan_lama = float(data_lama['total_perubahan'])
    total_lama = float(akun_tabungan_query['total'])

    if input_nama_akun_baru == akun_lama:
        if perubahan_baru != perubahan_lama:
            total_akhir = total_lama - perubahan_lama + perubahan_baru
        else:
            total_akhir = total_lama

        update_table(
            table='data_historis',
            data={
                'nama_akun': input_nama_akun_baru,
                'kategori': input_kategori_baru,
                'sub_kategori': input_sub_kategori_baru,
                'total_perubahan': perubahan_baru,
                'tanggal': input_tanggal_baru
            },
            eq_col='id', eq_row=id
        )
        update_table(
            table='akun_tabungan',
            data={'total': total_akhir},
            eq_col='nama_akun', eq_row=input_nama_akun_baru
        )

    else:
        data_baru = select_table(table='akun_tabungan', eq_col='nama_akun', eq_row=input_nama_akun_baru)[0]
        total_akun_baru = data_baru['total']

        total_akhir_lama = total_lama - perubahan_lama
        total_akhir_baru = total_akun_baru + perubahan_baru

        update_table(
            table='data_historis',
            data={
                'nama_akun': input_nama_akun_baru,
                'kategori': input_kategori_baru,
                'sub_kategori': input_sub_kategori_baru,
                'total_perubahan': perubahan_baru,
                'tanggal': input_tanggal_baru
            },
            eq_col='id', eq_row=id
        )

        update_table(
            table='akun_tabungan',
            data={'total': total_akhir_lama},
            eq_col='nama_akun', eq_row=akun_lama
        )

        update_table(
            table='akun_tabungan',
            data={'total': total_akhir_baru},
            eq_col='nama_akun', eq_row=input_nama_akun_baru
        )

    session.pop('edit_histori_data', None)
    session.pop('edit_histori_id', None)

    return redirect(url_for('histori.histori'))

@histori_bp.route('/hapus_histori/<id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    data_lama = select_table(table='data_historis', eq_col='id', eq_row=id)[0]

    akun = data_lama['nama_akun']
    total_lama = float(data_lama['total_perubahan'])

    data_akun = select_table(table='akun_tabungan', eq_col='nama_akun', eq_row=akun)[0]
    total_awal = data_akun['total']
    total_akhir = total_awal - total_lama

    update_table(
        table='akun_tabungan',
        data={"total": total_akhir},
        eq_col='nama_akun', eq_row=akun
    )
    delete_table(table='data_historis', eq_col='id', eq_row=id)
    return redirect(url_for('histori.histori'))