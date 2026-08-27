from flask import Blueprint, render_template, redirect, request, url_for, session
from functools import wraps
from app import supabase
from datetime import date

histori_bp = Blueprint('histori', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.auth'))
        return f(*args, **kwargs)
    return decorated_function

@histori_bp.route('/histori', methods=['GET'])
@login_required
def histori():
    edit_histori = None
    edit_histori_id = request.args.get('edit_histori_id')
    if edit_histori_id:
        response = supabase.table('data_historis').select('*').eq('id', edit_histori_id).execute()
        if response.data:
            edit_histori = response.data[0]

    response = supabase.table('akun_tabungan').select('total').execute()
    total_saldo = 0
    if response.data:
        for akun in response.data:
            total_saldo += float(akun['total'])
        total_saldo = f"Rp {total_saldo:,.2f}"
    else:
        total_saldo = "Belum ada akun tabungan yang terdaftar"

    response = supabase.table('data_historis').select('total_perubahan').eq('jenis', 'Pengeluaran').execute()
    total_pengeluaran = 0
    if response.data:
        for akun in response.data:
            total_pengeluaran += float(akun['total_perubahan'])
    else:
        total_pengeluaran = 0

    response = supabase.table('data_historis').select('total_perubahan').eq('jenis', 'Pemasukan').execute()
    total_pemasukan = 0
    if response.data:
        for akun in response.data:
            total_pemasukan += float(akun['total_perubahan'])
    else:
        total_pemasukan = 0

    response = supabase.table('akun_tabungan').select('nama_akun').execute().data
    akun_tabungan = response

    response = supabase.table('kategori').select('kategori').execute().data
    kategori = response

    response = supabase.table('data_historis').select('*').order('tanggal', desc=True).order('id', desc=True).execute()
    data_historis = response.data

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

    response = supabase.table('data_historis').select('*').eq('id', id).execute()
    data_lama = response.data[0]
    akun_lama = data_lama['nama_akun']
    perubahan_lama = float(data_lama['total_perubahan'])
    total_lama = float(data_lama['total_akhir'])

    if input_nama_akun_baru == akun_lama:
        if perubahan_baru != perubahan_lama:
            total_akhir = total_lama - perubahan_lama + perubahan_baru
        else:
            total_akhir = total_lama
        supabase.table('data_historis')\
                .upsert({
                    'id': id,
                    'nama_akun': input_nama_akun_baru,
                    'kategori': input_kategori_baru,
                    'sub_kategori': input_sub_kategori_baru,
                    'total_perubahan': perubahan_baru,
                    'total_akhir': total_akhir,
                    'tanggal': input_tanggal_baru
                }).execute()
        supabase.table('akun_tabungan')\
            .update({
                'total': total_akhir
            }).eq('nama_akun', input_nama_akun_baru).execute()
    else:
        response = supabase.table('akun_tabungan').select('*').eq('nama_akun', input_nama_akun_baru).execute()
        data_baru = response.data[0]
        total_akun_baru = data_baru['total']

        total_akhir_lama = total_lama - perubahan_lama
        total_akhir_baru = total_lama + perubahan_baru

        supabase.table('data_historis')\
                .upsert({
                    'id': id,
                    'nama_akun': input_nama_akun_baru,
                    'kategori': input_kategori_baru,
                    'sub_kategori': input_sub_kategori_baru,
                    'total_perubahan': perubahan_baru,
                    'total_akhir': total_akhir_baru,
                    'tanggal': input_tanggal_baru
                }).execute()
        supabase.table('akun_tabungan')\
            .upsert({
                'nama_akun': akun_lama,
                'total': total_akhir_lama
            }).execute()
        supabase.table('akun_tabungan')\
            .upsert({
                'nama_akun': input_nama_akun_baru,
                'total': total_akhir_baru
            }).execute()

    session.pop('edit_histori_data', None)
    session.pop('edit_histori_id', None)

    return redirect(url_for('histori.histori'))

@histori_bp.route('/hapus_histori/<id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    response = supabase.table('data_historis').select('*').eq('id', id).execute()
    data_lama = response.data[0]

    akun = data_lama['nama_akun']
    total_lama = float(data_lama['total_perubahan'])

    response = supabase.table('akun_tabungan').select('*').eq('nama_akun', akun).execute()
    data_akun = response.data[0]
    total_awal = data_akun['total']
    total_akhir = total_awal - total_lama

    supabase.table('akun_tabungan')\
        .update({
            "total": total_akhir
        }).eq('nama_akun', akun).execute()
    supabase.table('data_historis').delete().eq('id', id).execute()
    return redirect(url_for('histori.histori'))