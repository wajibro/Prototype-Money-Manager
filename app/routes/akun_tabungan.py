from flask import Blueprint, render_template, redirect, request, url_for, flash
from app import supabase
from datetime import date

akun_tabungan_bp = Blueprint('akun_tabungan', __name__)

@akun_tabungan_bp.route('/daftar_akun_tabungan', methods=['GET'])
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

    response = supabase.table('akun_tabungan').select('*').order('id', desc=False).execute()
    data_akun_tabungan = response.data

    return render_template('akun_tabungan.html', total_saldo=total_saldo, data_akun_tabungan=data_akun_tabungan, tab=tab, message=message)

@akun_tabungan_bp.route('/tambah_akun', methods=['GET', 'POST'])
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

        if total != 0:
            supabase.table('data_historis')\
                .insert({
                    "tanggal"           : date.today().isoformat(),
                    "nama_akun"         : nama_akun,
                    "jenis"             : "Tambah Akun",
                    "kategori"          : "Tambah Akun",
                    "total_perubahan"   : total,
                    "total_akhir"       : total
                }).execute()
        return redirect(url_for('akun_tabungan.akun_tabungan', tab='', message=''))        

@akun_tabungan_bp.route('/hapus_akun/<nama_akun>', methods=['POST'])
def delete(nama_akun):
    supabase.table('akun_tabungan').delete().eq('nama_akun', nama_akun).execute()
    supabase.table('data_historis').delete().eq('nama_akun', nama_akun).eq('jenis', "Tambah Akun").execute()
    return redirect(url_for('akun_tabungan.akun_tabungan', tab='', message=''))