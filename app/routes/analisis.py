from flask import Blueprint, render_template, redirect, request, url_for, session
from functools import wraps
from app import supabase
from datetime import date
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

analisis_bp = Blueprint('analisis', __name__)

GAYA_GARIS_AKUN = {
    'Cash upi': {'color': '#ff6b6b', 'marker': 'o'},
    'Shopee pino': {'color': '#ff922b', 'marker': 's'},
    'Bank pyno': {'color': '#339af0', 'marker': '^'}
}
WARNA_PIE = ['#ffc078', '#74c0fc', '#63e6be', '#94d82d']

FORMATTER_RUPIAH = ticker.FuncFormatter(lambda x, pos: f'Rp {x:,.0f}')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.auth'))
        return f(*args, **kwargs)
    return decorated_function

def grafik_ke_base64():
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', dpi=150)
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()
    return f"data:image/png;base64,{plot_url}"

@analisis_bp.route('/analisis')
@login_required
def analisis():
    response = supabase.table('data_historis').select('*').eq('jenis', 'Pengeluaran').execute()
    data = response.data

    daftar_kategori = set()
    daftar_kategori_masuk = sorted(list(set(p['kategori'] for p in data)))
    
    kategori_total = {kat: 0 for kat in daftar_kategori_masuk}

    sub_kategori_data = {}

    for p in data:
        kat = p['kategori']
        nominal = abs(p['total_perubahan'])

        if kat in kategori_total:
            kategori_total[kat] += nominal

        if kat not in sub_kategori_data:
            sub_kategori_data[kat] = {}
        sub_kat = p['sub_kategori']
        sub_kategori_data[kat][sub_kat] = sub_kategori_data[kat].get(sub_kat, 0) + nominal

    plt.figure(figsize=(14/len(kategori_total), 9/len(kategori_total)))
    kategori_nama = list(kategori_total.keys())
    nominal_kategori = list(kategori_total.values())
    bars = plt.bar(kategori_nama, nominal_kategori, color=['#ff6b6b']*3, edgecolor='black')

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 2000, f"Rp {yval:,}", ha='center', va='bottom', fontsize=9)

    ax1 = plt.gca()
    ax1.yaxis.set_major_formatter(FORMATTER_RUPIAH)
    plt.title('Total Pengeluaran Per Kategori Utama', fontsize=12, fontweight='bold')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    chart_batang_pengeluaran = grafik_ke_base64()

    fig, axes = plt.subplots(3, 1, figsize=(15, 30))
    kategori_list = daftar_kategori_masuk

    for i, kat in enumerate(kategori_list):
        sub_data = sub_kategori_data.get(kat, {})
        ax = axes[i]
        if sub_data and sum(sub_data.values()) > 0:
            labels_sub = list(sub_data.keys())
            values_sub = list(sub_data.values())
            ax.pie(
                values_sub, labels=labels_sub,
                autopct=lambda p: f'Rp {int(p*sum(values_sub)/100):,}\n({p:.1f}%)',
                startangle=140, colors=WARNA_PIE,
                wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}, textprops={'fontsize': 9}
            )
            ax.set_title(f'Sub-Kategori: {kat}', fontsize=11, fontweight='bold')
        else:
            ax.axis('off')

    plt.suptitle('Rincian Sub-Kategori Pengeluaran Dompet', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    chart_pie_pengeluaran = grafik_ke_base64()

    response_all = supabase.table('data_historis').select('*').execute()
    data_all = response_all.data
    data_sorted = sorted(data_all, key=lambda x: x['tanggal'])

    akun_tren = {}
    for p in data_sorted:
        nama_akun = p['nama_akun']
        if nama_akun not in akun_tren:
            akun_tren[nama_akun] = {'tanggal': [], 'total': []}
        akun_tren[nama_akun]['tanggal'].append(p['tanggal'])
        akun_tren[nama_akun]['total'].append(p['total_akhir'])

    plt.figure(figsize=(12, 5))

    for nama_akun, tren in akun_tren.items():
        gaya = GAYA_GARIS_AKUN.get(nama_akun, {'marker': 'o'})
        plt.plot(tren['tanggal'], tren['total'], label=nama_akun, linewidth=2.5, **gaya)
        plt.text(tren['tanggal'][-1], tren['total'][-1], f" Rp {tren['total'][-1]:,}", va='center', fontweight='bold', fontsize=9)

    ax3 = plt.gca()
    ax3.yaxis.set_major_locator(ticker.MultipleLocator(1000000))
    ax3.yaxis.set_major_formatter(FORMATTER_RUPIAH)
    plt.title('Tren Saldo Akhir Berdasarkan Akun', fontsize=12, fontweight='bold', pad=15)
    plt.xlabel('Tanggal Transaksi', fontsize=10)
    plt.legend(title="Daftar Akun", loc='upper left', frameon=True, shadow=True)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=15)
    plt.tight_layout()
    chart_garis = grafik_ke_base64()

    response = supabase.table('data_historis').select('*').eq('jenis', 'Pemasukan').execute()
    data = response.data

    daftar_kategori = set()
    daftar_kategori_masuk = sorted(list(set(p['kategori'] for p in data)))
    
    kategori_total = {kat: 0 for kat in daftar_kategori_masuk}
    sub_kategori_data = {}
    
    for p in data:
        kat = p['kategori']
        nominal = abs(p['total_perubahan'])

        if kat in kategori_total:
            kategori_total[kat] += nominal

        if kat not in sub_kategori_data:
            sub_kategori_data[kat] = {}
        sub_kat = p['sub_kategori']
        sub_kategori_data[kat][sub_kat] = sub_kategori_data[kat].get(sub_kat, 0) + nominal

    plt.figure(figsize=(14/len(kategori_total), 9/len(kategori_total)))
    kategori_nama = list(kategori_total.keys())
    nominal_kategori = list(kategori_total.values())
    bars = plt.bar(kategori_nama, nominal_kategori, color=['#ff6b6b']*3, edgecolor='black')

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 2000, f"Rp {yval:,}", ha='center', va='bottom', fontsize=9)

    ax1 = plt.gca()
    ax1.yaxis.set_major_formatter(FORMATTER_RUPIAH)
    plt.title('Total Pemasukan Per Kategori Utama', fontsize=12, fontweight='bold')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    chart_batang_pemasukan = grafik_ke_base64()

    fig, axes = plt.subplots(3, 1, figsize=(15, 30))
    kategori_list = daftar_kategori_masuk

    for i, kat in enumerate(kategori_list):
        sub_data = sub_kategori_data.get(kat, {})
        ax = axes[i]
        if sub_data and sum(sub_data.values()) > 0:
            labels_sub = list(sub_data.keys())
            values_sub = list(sub_data.values())
            ax.pie(
                values_sub, labels=labels_sub,
                autopct=lambda p: f'Rp {int(p*sum(values_sub)/100):,}\n({p:.1f}%)',
                startangle=140, colors=WARNA_PIE,
                wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}, textprops={'fontsize': 9}
            )
            ax.set_title(f'Sub-Kategori: {kat}', fontsize=11, fontweight='bold')
        else:
            ax.axis('off')

    plt.suptitle('Rincian Sub-Kategori Pengeluaran Dompet', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    chart_pie_pemasukan = grafik_ke_base64()

    return render_template('analisis.html', chart_batang_pengeluaran=chart_batang_pengeluaran, chart_batang_pemasukan=chart_batang_pemasukan, chart_pie_pengeluaran=chart_pie_pengeluaran, chart_pie_pemasukan=chart_pie_pemasukan, chart_garis=chart_garis)