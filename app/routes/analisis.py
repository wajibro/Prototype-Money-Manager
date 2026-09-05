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

    total_awal = 8974628

    data = select_table(table='data_historis')

    tanggal_query = sorted(list(set(p['tanggal'] for p in data)))
    tanggal = [datetime.strptime(p, '%Y-%m-%d') for p in tanggal_query]

    tanggal_terpisah = []
    cashflow_per_hari = []
    for p in tanggal:
        per_tanggal = select_table(table='data_historis', eq_col='tanggal', eq_row=p)
        tanggal_terpisah.append(per_tanggal)

        total_pemasukan_x = 0
        total_pengeluaran_x = 0

        for r in per_tanggal:
            if r['jenis'] == 'Pemasukan':
                total_pemasukan_x += r['total_perubahan']
            elif r['jenis'] == 'Pengeluaran':
                total_pengeluaran_x += r['total_perubahan']

        cash_flow = total_pemasukan_x + total_pengeluaran_x
        cashflow_per_hari.append(cash_flow)

    x = total_awal
    saldo_historikal = []
    for u, v in zip(cashflow_per_hari, tanggal):
        x += u
        saldo_historikal.append(x)

    FORMATTER_RUPIAH = ticker.FuncFormatter(lambda x, pos: f'Rp {x:,.0f}')

    plt.figure(figsize=(12, 6))

    plt.plot(tanggal, saldo_historikal, label='Total Saldo', linewidth=3, 
            color='#2b8a3e', marker='o', markersize=8, 
            markeredgecolor='white', markeredgewidth=1.5)

    plt.fill_between(tanggal, saldo_historikal, alpha=0.15, color='#2b8a3e')

    for date, saldo in zip(tanggal, saldo_historikal):
        plt.text(date, saldo + (max(saldo_historikal) * 0.01), 
                f'Rp {saldo:,.0f}', 
                ha='center', va='bottom', 
                fontsize=9, fontweight='bold', rotation=30,
                bbox=dict(
                    boxstyle='round,pad=0.3', 
                    facecolor='white', alpha=0.8, 
                    edgecolor='#2b8a3e'
                ))

    plt.text(tanggal[-1], saldo_historikal[-1] + (max(saldo_historikal) * 0.02), 
            f'Rp {saldo_historikal[-1]:,}', 
            va='center', fontweight='bold', fontsize=11,
            bbox=dict(
                boxstyle='round,pad=0.4', 
                facecolor='#2b8a3e', alpha=0.15, 
                edgecolor='#2b8a3e'
            ))

    ax = plt.gca()
    ax.yaxis.set_major_locator(ticker.MultipleLocator(1000000))
    ax.yaxis.set_major_formatter(FORMATTER_RUPIAH)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.tick_params(axis='both', labelsize=9)
    ax.set_facecolor('#f8f9fa')
    ax.grid(True, linestyle='--', alpha=0.6, color='#ced4da')

    plt.title('Tren Total Saldo Keseluruhan', fontsize=14, fontweight='bold', 
            pad=20, color='#1a1a1a')
    plt.xlabel('Tanggal Transaksi', fontsize=11, fontweight='500')
    plt.ylabel('Total Saldo', fontsize=11, fontweight='500')
    plt.xticks(rotation=20, ha='right')
    plt.tight_layout()
    chart_cashflow = grafik_ke_base64()

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
        chart_cashflow          = chart_cashflow
    )