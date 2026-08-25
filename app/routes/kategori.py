from flask import Blueprint, render_template, redirect, request, url_for, flash
from app import supabase
from datetime import date

kategori_bp = Blueprint('kategori', __name__) 

@kategori_bp.route('/kategori', methods=['GET'])
def kategori():
    tab_aktif = request.args.get('tab', 'pengeluaran')
    message = request.args.get('message', '')

    response = supabase.table('akun_tabungan').select('total').execute()
    total_saldo = 0
    if response.data:
        for akun in response.data:
            total_saldo += float(akun['total'])
        total_saldo = f"Rp {total_saldo:,.2f}"
    else:
        total_saldo = "Belum ada akun tabungan yang terdaftar"

    response = supabase.table('kategori').select('*').execute()
    kategori = response.data

    response = supabase.table('akun_tabungan').select('*').execute()
    akun_tabungan = response.data

    return render_template('kategori.html', total_saldo=total_saldo ,kategori=kategori, akun_tabungan=akun_tabungan, tab_aktif=tab_aktif, message=message)

@kategori_bp.route('/simpan_pengeluaran', methods=['GET', 'POST'])
def simpan_pengeluaran():
    input_tanggal                 = request.form.get('input_tanggal')
    input_kategori_pengeluaran    = request.form.get('input_kategori_pengeluaran')
    input_akun_tabungan           = request.form.get('input_akun_tabungan')
    input_total_perubahan         = request.form.get('input_total_perubahan')

    total_perubahan = float(input_total_perubahan)
    response = supabase.table('akun_tabungan').select('total').eq('nama_akun', input_akun_tabungan).execute()
    total_tabungan = float(response.data[0]['total'])

    total_akhir = total_tabungan - total_perubahan

    if input_kategori_pengeluaran and input_akun_tabungan and input_total_perubahan:
        supabase.table('data_historis')\
        .insert({
            "tanggal"           : input_tanggal,
            "nama_akun"         : input_akun_tabungan,
            "jenis"             : "Pengeluaran",
            "kategori"          : input_kategori_pengeluaran,
            "total_perubahan"   : -total_perubahan,
            "total_akhir"       : total_akhir
        }).execute()
        supabase.table('akun_tabungan')\
        .update({
            "total": total_akhir
        }).eq('nama_akun', input_akun_tabungan).execute()

        return redirect(url_for('kategori.kategori'))

@kategori_bp.route('/simpan_pemasukan', methods=['GET', 'POST'])
def simpan_pemasukan():
    input_tanggal                 = request.form.get('input_tanggal')
    input_kategori_pemasukan      = request.form.get('input_kategori_pemasukan')
    input_akun_tabungan           = request.form.get('input_akun_tabungan')
    input_total_perubahan         = request.form.get('input_total_perubahan')

    total_perubahan = float(input_total_perubahan)
    response = supabase.table('akun_tabungan').select('total').eq('nama_akun', input_akun_tabungan).execute()
    total_tabungan = float(response.data[0]['total'])

    total_akhir = total_tabungan + total_perubahan

    if input_kategori_pemasukan and input_akun_tabungan and input_total_perubahan:
        supabase.table('data_historis')\
        .insert({
            "tanggal"           : input_tanggal,
            "nama_akun"         : input_akun_tabungan,
            "jenis"             : "Pemasukan",
            "kategori"          : input_kategori_pemasukan,
            "total_perubahan"   : total_perubahan,
            "total_akhir"       : total_akhir
        }).execute()
        supabase.table('akun_tabungan')\
        .update({
            "total": total_akhir
        }).eq('nama_akun', input_akun_tabungan).execute()

    return redirect(url_for('kategori.kategori'))

@kategori_bp.route('/tambah_kategori_pengeluaran', methods=['GET', 'POST'])
def tambah_kategori_pengeluaran():
    input_kategori_baru = request.form.get('input_kategori_pengeluaran_baru')

    kategori_baru = input_kategori_baru.capitalize()

    response = supabase.table('kategori').select('*').eq('kategori', kategori_baru).execute()

    if response.data and len(response.data) > 0:
        return redirect(url_for('kategori.kategori', tab="tambah_kategori_pengeluaran", message="Kategori yang sama sudah ada, silahkan buat yang baru"))

    if input_kategori_baru:
        supabase.table('kategori')\
            .insert({
                "kategori"  : kategori_baru,
                "jenis"     : "Pengeluaran"
            }).execute()
        return redirect(url_for('kategori.kategori', tab='pengeluaran'))

@kategori_bp.route('/tambah_kategori_pemasukan', methods=['GET', 'POST'])
def tambah_kategori_pemasukan():
    input_kategori_baru = request.form.get('input_kategori_pemasukan_baru')

    kategori_baru = input_kategori_baru.capitalize()

    response = supabase.table('kategori').select('*').eq('kategori', kategori_baru).execute()

    if response.data and len(response.data) > 0:
        return redirect(url_for('kategori.kategori', tab="tambah_kategori_pengeluaran", message="Kategori yang sama sudah ada, silahkan buat yang baru"))

    if input_kategori_baru:
        supabase.table('kategori')\
            .insert({
                "kategori"  : kategori_baru,
                "jenis"     : "Pemasukan"
            }).execute()
        return redirect(url_for('kategori.kategori', tab='pemasukan'))