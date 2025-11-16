# tentativa de carregar o csv e gerar quatro gráficos
# versão estável para windows com caminhos configuráveis

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------------------------------------
# configurações básicas
# ----------------------------------------------------------

# crie suas pastas para o arquivo csv e para o output, deixei as minhas como exemplo

csv_path = r"C:\Users\stcha\Documents\PUCC_Visão_Computacional\20251029-220949_Walk.csv"
out_dir = r"C:\Users\stcha\Documents\PUCC_Visão_Computacional\resultados_csv_graficos"

os.makedirs(out_dir, exist_ok=True)

# ----------------------------------------------------------
# carregar csv
# ----------------------------------------------------------
if not os.path.exists(csv_path):
    raise FileNotFoundError(f"arquivo csv não encontrado: {csv_path}")

df = pd.read_csv(csv_path)
print("colunas:", list(df.columns[:40]))

# ----------------------------------------------------------
# detectar colunas de tornozelo
# ----------------------------------------------------------
def encontrar_coluna(padroes):
    for c in df.columns:
        texto = c.lower()
        if all(p in texto for p in padroes):
            return c
    return None

col_l = encontrar_coluna(['l','ankle','y'])
col_r = encontrar_coluna(['r','ankle','y'])

# fallback
if col_l is None:
    for c in df.columns:
        if 'l_ankle' in c.lower():
            col_l = c
            break

if col_r is None:
    for c in df.columns:
        if 'r_ankle' in c.lower():
            col_r = c
            break

if col_l is None or col_r is None:
    raise RuntimeError("não foi possível detectar as colunas dos tornozelos")

print("usando colunas:", col_l, col_r)

# ----------------------------------------------------------
# detectar coluna de tempo
# ----------------------------------------------------------
col_tempo = None
for cand in ['time','timestamp','frame','frame_id','Time','frameNumber']:
    if cand in df.columns:
        col_tempo = cand
        break

if col_tempo is None:
    for c in df.columns:
        if np.issubdtype(df[c].dtype, np.number) and c not in [col_l, col_r]:
            col_tempo = c
            break

tempo_raw = df[col_tempo].astype(float).values

# inferir fps
dts = np.diff(tempo_raw)
med_dt = np.median(dts) if len(dts)>0 else 1.0

if med_dt <= 0:
    fps = 30.0
    tempo_s = np.arange(len(df)) / fps
elif med_dt == 1:
    fps = 30.0
    tempo_s = (tempo_raw - tempo_raw[0]) / fps
elif med_dt > 1000:
    tempo_s = (tempo_raw - tempo_raw[0]) / 1000.0
    fps = 1.0 / np.median(np.diff(tempo_s))
else:
    tempo_s = tempo_raw - tempo_raw[0]
    fps = 1.0/med_dt

print(f"fps inferido: {fps:.2f}, duração: {tempo_s[-1]:.2f}s")

# ----------------------------------------------------------
# extrair e filtrar sinais
# ----------------------------------------------------------
y_l = pd.to_numeric(df[col_l], errors='coerce').values
y_r = pd.to_numeric(df[col_r], errors='coerce').values

def preencher_nan(x):
    n = len(x)
    idx = np.arange(n)
    ok = np.isfinite(x)
    if not ok.any():
        return np.zeros_like(x)
    return np.interp(idx, idx[ok], x[ok])

y_l = preencher_nan(y_l)
y_r = preencher_nan(y_r)

# filtragem
usa_scipy = True
try:
    from scipy import signal
except:
    usa_scipy = False

if usa_scipy:
    try:
        y_l_med = signal.medfilt(y_l, kernel_size=5)
        y_r_med = signal.medfilt(y_r, kernel_size=5)

        nyq = 0.5 * fps
        cutoff = min(6.0, 0.4*nyq)

        if cutoff > 0.5:
            b,a = signal.butter(4, cutoff/nyq, btype='low')
            y_l_f = signal.filtfilt(b,a,y_l_med)
            y_r_f = signal.filtfilt(b,a,y_r_med)
        else:
            y_l_f = y_l_med
            y_r_f = y_r_med

    except:
        janela = int(max(3, round(fps/5)))
        y_l_f = pd.Series(y_l).rolling(janela, center=True, min_periods=1).mean()
        y_r_f = pd.Series(y_r).rolling(janela, center=True, min_periods=1).mean()

else:
    janela = int(max(3, round(fps/5)))
    y_l_f = pd.Series(y_l).rolling(janela, center=True, min_periods=1).mean()
    y_r_f = pd.Series(y_r).rolling(janela, center=True, min_periods=1).mean()

# ----------------------------------------------------------
# detectar picos
# ----------------------------------------------------------
if usa_scipy:
    prom_l = max(0.01, 0.2*np.std(y_l_f))
    prom_r = max(0.01, 0.2*np.std(y_r_f))
    try:
        picos_l, _ = signal.find_peaks(y_l_f, prominence=prom_l, distance=int(0.4*fps))
        picos_r, _ = signal.find_peaks(y_r_f, prominence=prom_r, distance=int(0.4*fps))
    except:
        picos_l = np.where((y_l_f[1:-1] > y_l_f[:-2]) & (y_l_f[1:-1] > y_l_f[2:]))[0] + 1
        picos_r = np.where((y_r_f[1:-1] > y_r_f[:-2]) & (y_r_f[1:-1] > y_r_f[2:]))[0] + 1
else:
    picos_l = np.where((y_l_f[1:-1] > y_l_f[:-2]) & (y_l_f[1:-1] > y_l_f[2:]))[0] + 1
    picos_r = np.where((y_r_f[1:-1] > y_r_f[:-2]) & (y_r_f[1:-1] > y_r_f[2:]))[0] + 1

print(f"picos detectados: esquerdo {len(picos_l)}, direito {len(picos_r)}")

# ----------------------------------------------------------
# cadência com janela deslizante
# ----------------------------------------------------------
janela_s = 10.0
janela_frames = max(1, int(janela_s * fps))
cad = np.zeros(len(df))
metade = janela_frames // 2

for i in range(len(df)):
    s = max(0, i - metade)
    e = min(len(df), i + metade)
    passos = np.sum((picos_l >= s) & (picos_l < e)) + np.sum((picos_r >= s) & (picos_r < e))
    dur = max(1e-6, tempo_s[e-1] - tempo_s[s])
    cad[i] = (passos / dur) * 60.0

# ----------------------------------------------------------
# índice de simetria
# ----------------------------------------------------------
tempos_pares = []
si_pares = []

for pl in picos_l:
    if len(picos_r) == 0:
        break
    idx = np.argmin(np.abs(picos_r - pl))
    if abs(picos_r[idx] - pl) <= int(0.6 * fps):
        al = y_l_f[pl]
        ar = y_r_f[picos_r[idx]]
        denom = 0.5 * (abs(al) + abs(ar)) if abs(al)+abs(ar) > 0 else 1e-6
        si = abs(al - ar) / denom * 100.0
        tempos_pares.append(tempo_s[pl])
        si_pares.append(si)

# ----------------------------------------------------------
# dataframe com picos
# ----------------------------------------------------------
df_picos = pd.DataFrame({
    "tempo_s": np.concatenate((tempo_s[picos_l], tempo_s[picos_r])),
    "lado": ["E"]*len(picos_l) + ["D"]*len(picos_r),
    "amplitude": np.concatenate((y_l_f[picos_l], y_r_f[picos_r]))
}).sort_values("tempo_s").reset_index(drop=True)

# ----------------------------------------------------------
# caminhos de saída
# ----------------------------------------------------------
fig1 = os.path.join(out_dir, "trajetoria_picos.png")
fig2 = os.path.join(out_dir, "cadencia.png")
fig3 = os.path.join(out_dir, "simetria.png")
fig4 = os.path.join(out_dir, "autocorrelacao.png")
csv_out = os.path.join(out_dir, "picos_resumo.csv")

# ----------------------------------------------------------
# gráfico 1 – trajetória do tornozelo
# ----------------------------------------------------------
plt.figure(figsize=(12,4))
plt.plot(tempo_s, y_l, label="esquerdo_bruto")
plt.plot(tempo_s, y_r, label="direito_bruto")
plt.plot(tempo_s, y_l_f, label="esquerdo_filtrado")
plt.plot(tempo_s, y_r_f, label="direito_filtrado")
plt.scatter(tempo_s[picos_l], y_l_f[picos_l], color="blue", marker='o')
plt.scatter(tempo_s[picos_r], y_r_f[picos_r], color="red", marker='x')
plt.xlabel("tempo (s)")
plt.ylabel("posição vertical")
plt.title("trajetória vertical dos tornozelos com picos detectados")
plt.legend()
plt.tight_layout()
plt.savefig(fig1, dpi=300)
plt.close()

# ----------------------------------------------------------
# gráfico 2 – cadência
# ----------------------------------------------------------
plt.figure(figsize=(12,4))
plt.plot(tempo_s, cad)
plt.xlabel("tempo (s)")
plt.ylabel("cadência (passos/min)")
plt.title("cadência estimada (janela de 10 s)")
plt.tight_layout()
plt.savefig(fig2, dpi=300)
plt.close()

# ----------------------------------------------------------
# gráfico 3 – índice de simetria
# ----------------------------------------------------------
plt.figure(figsize=(12,4))
if tempos_pares:
    plt.plot(tempos_pares, si_pares, marker='o')
plt.xlabel("tempo (s)")
plt.ylabel("índice de simetria (%)")
plt.title("índice de simetria entre passos")
plt.tight_layout()
plt.savefig(fig3, dpi=300)
plt.close()

# ----------------------------------------------------------
# gráfico 4 – autocorrelação
# ----------------------------------------------------------
def autocorrelacao(x, nlags=200):
    x = x - np.mean(x)
    corr = np.correlate(x, x, mode="full")
    meio = len(corr) // 2
    ac = corr[meio:meio+nlags]
    ac = ac / ac[0]
    return ac

nlags = min(200, len(y_l_f) // 2)
ac = autocorrelacao(y_l_f, nlags)
lags = np.arange(len(ac)) / fps

plt.figure(figsize=(12,4))
plt.plot(lags, ac)
plt.xlabel("defasagem (s)")
plt.ylabel("autocorrelação")
plt.title("autocorrelação do sinal vertical do tornozelo esquerdo")
plt.tight_layout()
plt.savefig(fig4, dpi=300)
plt.close()

# ----------------------------------------------------------
# salvar csv
# ----------------------------------------------------------
df_picos.to_csv(csv_out, index=False)

# ----------------------------------------------------------
# saída final
# ----------------------------------------------------------
print("\nfiguras salvas:")
print(fig1)
print(fig2)
print(fig3)
print(fig4)
print("csv salvo:", csv_out)
