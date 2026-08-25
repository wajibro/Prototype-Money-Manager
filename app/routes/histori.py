from flask import Blueprint, render_template, redirect, request, url_for, flash
from app import supabase
from datetime import date

histori_bp = Blueprint('histori', __name__)

@histori_bp.route('/histori', methods=['GET'])
def histori():
    response = supabase.table('akun_tabungan').select('total').execute()
    total_saldo = 0
    if response.data:
        for akun in response.data:
            total_saldo += float(akun['total'])
        total_saldo = f"Rp {total_saldo:,.2f}"
    else:
        total_saldo = "Belum ada akun tabungan yang terdaftar"

    response = supabase.table('data_historis').select('*').order('tanggal', desc=True).execute()
    data_historis = response.data

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

    return render_template('histori.html', total_saldo=total_saldo, total_pengeluaran=total_pengeluaran, total_pemasukan=total_pemasukan, data_historis=data_historis)

@histori_bp.route('/hapus_histori/<id>', methods=['GET', 'POST'])
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