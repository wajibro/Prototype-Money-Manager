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

    data = select_table(table='data_historis')
    
    # Ambil saldo awal dari data 'Tambah Akun' pada tanggal 2026-08-25
    tambah_akun_data = [p for p in data if p['tanggal'] == "2026-08-25" and p['jenis'] == 'Tambah Akun']
    saldo_awal = 0
    for record in tambah_akun_data:
        saldo_awal += float(record['total_perubahan'])
    
    # Jika tidak ada data tambah akun, gunakan saldo awal default
    if saldo_awal == 0:
        saldo_awal = 6721236.0  # Default dari kode sebelumnya
    
    # Kelompokkan data berdasarkan tanggal (mulai dari 2026-08-25)
    data_by_date = {}
    for record in data:
        tanggal = record['tanggal']
        if tanggal not in data_by_date:
            data_by_date[tanggal] = []
        data_by_date[tanggal].append(record)
    
    # Urutkan tanggal
    tanggal_urut = sorted(data_by_date.keys())
    
    # Hitung saldo kumulatif per tanggal
    saldo_per_tanggal = []
    saldo_berjalan = saldo_awal
    
    # Tambahkan saldo awal pada tanggal 25
    saldo_per_tanggal.append({
        'tanggal': '2026-08-25',
        'saldo': saldo_berjalan
    })
    
    # Proses setiap tanggal setelah 25
    for tanggal in tanggal_urut:
        # Jika tanggal 25, skip karena sudah ditambahkan
        if tanggal == '2026-08-25':
            continue
        
        # Hitung total perubahan untuk tanggal ini
        total_perubahan = 0
        for record in data_by_date[tanggal]:
            # Tambahkan perubahan (negatif untuk pengeluaran, positif untuk pemasukan)
            total_perubahan += float(record['total_perubahan'])
        
        # Update saldo berjalan
        saldo_berjalan += total_perubahan
        
        # Simpan saldo per tanggal
        saldo_per_tanggal.append({
            'tanggal': tanggal,
            'saldo': saldo_berjalan
        })
    
    # Buat grafik
    if len(saldo_per_tanggal) > 1:
        # Siapkan data untuk plotting
        dates = [datetime.strptime(d['tanggal'], '%Y-%m-%d') for d in saldo_per_tanggal]
        saldos = [d['saldo'] for d in saldo_per_tanggal]
        
        plt.figure(figsize=(12, 6))
        
        # Plot garis dengan area fill
        plt.plot(dates, saldos, label='Total Saldo', linewidth=3, 
                color='#2b8a3e', marker='o', markersize=8, 
                markeredgecolor='white', markeredgewidth=1.5)
        
        # Fill area di bawah grafik
        plt.fill_between(dates, saldos, alpha=0.15, color='#2b8a3e')
        
        # Tambahkan label nilai di setiap titik
        for date, saldo in zip(dates, saldos):
            plt.text(date, saldo + (max(saldos) * 0.01), 
                    f'Rp {saldo:,.0f}', 
                    ha='center', va='bottom', 
                    fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', 
                             facecolor='white', alpha=0.8, 
                             edgecolor='#2b8a3e'))
        
        # Highlight titik akhir
        plt.text(dates[-1], saldos[-1] + (max(saldos) * 0.02), 
                f'Rp {saldos[-1]:,}', 
                va='center', fontweight='bold', fontsize=11,
                bbox=dict(boxstyle='round,pad=0.4', 
                         facecolor='#2b8a3e', alpha=0.15, 
                         edgecolor='#2b8a3e'))
        
        # Format grafik
        ax = plt.gca()
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1000000))
        ax.yaxis.set_major_formatter(FORMATTER_RUPIAH)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.tick_params(axis='both', labelsize=9)
        ax.set_facecolor('#f8f9fa')
        ax.grid(True, linestyle='--', alpha=0.6, color='#ced4da')
        
        # Label dan judul
        plt.title('Tren Total Saldo Keseluruhan', fontsize=14, fontweight='bold', 
                 pad=20, color='#1a1a1a')
        plt.xlabel('Tanggal Transaksi', fontsize=11, fontweight='500')
        plt.ylabel('Total Saldo', fontsize=11, fontweight='500')
        plt.xticks(rotation=20, ha='right')
        plt.tight_layout()
        
        chart_cashflow = grafik_ke_base64()
    else:
        # Jika data tidak cukup
        chart_cashflow = None    
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