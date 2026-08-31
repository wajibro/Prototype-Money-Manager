from flask import Blueprint, render_template, redirect, request, url_for, session
from functools import wraps
from app import supabase
from datetime import date, datetime
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates

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

@analisis_bp.route('/analisis')
@login_required
def analisis():
    saldo_awal = 0
    total_saldo_query = select_table(table='akun_tabungan', select='total')
    total_saldo = 0
    if total_saldo_query:
        for akun in total_saldo_query:
            total_saldo += float(akun['total'])
        saldo_awal += total_saldo
        print(saldo_awal)
        total_saldo = f"Rp {total_saldo:,.2f}"
    else:
        total_saldo = "Belum ada akun tabungan yang terdaftar"

    total_pengeluaran_query = select_table(table='data_historis', select='total_perubahan', eq_col='jenis', eq_row='Pengeluaran')
    total_pengeluaran = 0
    if total_pengeluaran_query:
        for akun in total_pengeluaran_query:
            total_pengeluaran += float(akun['total_perubahan'])
        saldo_awal -= total_pengeluaran
        total_pengeluaran = f"Rp {total_pengeluaran:,.2f}"
    else:
        total_pengeluaran = 0

    total_pemasukan_query = select_table(table='data_historis', select='total_perubahan', eq_col='jenis', eq_row='Pemasukan')
    total_pemasukan = 0
    if total_pemasukan_query:
        for akun in total_pemasukan_query:
            total_pemasukan += float(akun['total_perubahan'])
        saldo_awal -= total_pemasukan
        total_pemasukan = f"Rp {total_pemasukan:,.2f}"
    else:
        total_pemasukan = 0

    all_tren = [saldo_awal]
    data = select_table(table='data_historis')
    tanggal = sorted(list(set(p['tanggal'] for p in data)))

    data_urut = sorted(data, key=lambda x: x['tanggal'])

    saldo_berjalan = saldo_awal
    tanggal_terakhir = None

    for record in data_urut:
        if record['tanggal'] == "2026-08-25":
            continue
        
        if record['tanggal'] != tanggal_terakhir:
            all_tren.append(saldo_berjalan)
            tanggal_terakhir = record['tanggal']
        
        saldo_berjalan += float(record['total_perubahan'])

    all_tren.append(saldo_berjalan)


    if tanggal and all_tren:
        date_total_pairs = sorted(
            [(datetime.strptime(d, '%Y-%m-%d'), t) for d, t in zip(tanggal, all_tren[1:])],
            key=lambda x: x[0]
        )
        
        if date_total_pairs:
            sorted_dates, sorted_totals = zip(*date_total_pairs)
            
            plt.figure(figsize=(12, 6))
            plt.plot(sorted_dates, sorted_totals, label='Total Saldo', linewidth=3, color='#2b8a3e', marker='o', markersize=6, markeredgecolor='white', markeredgewidth=1.5)

            offset = max(sorted_totals) * 0.02
            plt.text(sorted_dates[-1], sorted_totals[-1], f"  Rp {sorted_totals[-1]:,}", 
                    va='center', fontweight='bold', fontsize=10,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#2b8a3e', alpha=0.15, edgecolor='#2b8a3e'))

            for date, total in zip(sorted_dates, sorted_totals):
                plt.text(date, total+offset, f"Rp {total:,}", 
                        va='bottom' if total > 0 else 'top', ha='center', fontsize=7,
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

            ax = plt.gca()
            ax.yaxis.set_major_locator(ticker.MultipleLocator(1000000))
            ax.yaxis.set_major_formatter(FORMATTER_RUPIAH)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator())
            ax.tick_params(axis='both', labelsize=9)
            ax.set_facecolor('#f8f9fa')
            ax.grid(True, linestyle='--', alpha=0.6, color='#ced4da')

            plt.fill_between(sorted_dates, sorted_totals, alpha=0.15, color='#2b8a3e')

            plt.title('Tren Total Saldo Keseluruhan', fontsize=14, fontweight='bold', pad=20, color='#1a1a1a')
            plt.xlabel('Tanggal Transaksi', fontsize=11, fontweight='500')
            plt.ylabel('Total Saldo', fontsize=11, fontweight='500')
            plt.xticks(rotation=20, ha='right')
            plt.tight_layout()
            chart_cashflow = grafik_ke_base64()
        else:
            chart_cashflow = None
    else:
        chart_cashflow = None
    
    data_all = select_table(table='data_historis')
    
    data_sorted = sorted(data_all, key=lambda x: x['tanggal'])
    
    akun_tren = {}
    for p in data_sorted:
        nama_akun = p['nama_akun']
        if nama_akun not in akun_tren:
            akun_tren[nama_akun] = {'tanggal': [], 'total': []}
        akun_tren[nama_akun]['tanggal'].append(p['tanggal'])
        akun_tren[nama_akun]['total'].append(p['total_akhir'])
    
    plt.figure(figsize=(10, 5))
    
    for nama_akun, tren in akun_tren.items():
        date_total_pairs = sorted(
            [(datetime.strptime(d, '%Y-%m-%d'), t) for d, t in zip(tren['tanggal'], tren['total'])],
            key=lambda x: x[0]
        )
        
        if date_total_pairs:
            sorted_dates, sorted_totals = zip(*date_total_pairs)
        
            gaya = GAYA_GARIS_AKUN.get(nama_akun, {'marker': 'o'})
            plt.plot(sorted_dates, sorted_totals, label=nama_akun, linewidth=2.5, **gaya)
            
            for i, (date, total) in enumerate(zip(sorted_dates, sorted_totals)):
                if i == 0 or i == len(sorted_dates) - 1:
                    offset = max(sorted_totals) * 0.02
                    
                    if i == 0:
                        plt.text(date, total - offset, f"Rp {total:,.0f}", ha='center', va='top', fontweight='bold', fontsize=8)
                    else:
                        plt.text(date, total + offset, f"Rp {total:,.0f}", ha='center', va='bottom', fontweight='bold', fontsize=8)
    
    ax3 = plt.gca()
    ax3.yaxis.set_major_locator(ticker.MultipleLocator(1000000))
    ax3.yaxis.set_major_formatter(FORMATTER_RUPIAH)

    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax3.xaxis.set_major_locator(mdates.DayLocator())
    
    plt.title('Tren Saldo Akhir Berdasarkan Akun', fontsize=12, fontweight='bold', pad=15)
    plt.xlabel('Tanggal Transaksi', fontsize=10)
    plt.legend(title="Daftar Akun", loc='center left', bbox_to_anchor=(1, 0.5), frameon=True, shadow=True)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=15)
    plt.tight_layout()
    chart_garis = grafik_ke_base64()

    data = select_table(table='data_historis', eq_col='jenis', eq_row='Pengeluaran')

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

    plt.figure(figsize=(10, 6))
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

    kategori_list = daftar_kategori_masuk
    fig, axes = plt.subplots(len(kategori_list), 1, figsize=(12, 5*len(kategori_list)))

    if len(kategori_list) == 1:
        axes = [axes]

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

    data = select_table(table='data_historis', eq_col='jenis', eq_row='Pemasukan')

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

    kategori_list = daftar_kategori_masuk
    fig, axes = plt.subplots(len(kategori_list), 1, figsize=(12, 5*len(kategori_list)))

    if len(kategori_list) == 1:
        axes = [axes]
    
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

    return render_template(
        'analisis.html',
        total_saldo             = total_saldo,
        total_pengeluaran       = total_pengeluaran,
        total_pemasukan         = total_pemasukan,
        chart_batang_pengeluaran= chart_batang_pengeluaran,
        chart_batang_pemasukan  = chart_batang_pemasukan,
        chart_pie_pengeluaran   = chart_pie_pengeluaran,
        chart_pie_pemasukan     = chart_pie_pemasukan,
        chart_garis             = chart_garis,
        chart_cashflow          = chart_cashflow
    )