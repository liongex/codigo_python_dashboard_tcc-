import sys
import sqlite3
import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont

# Configura o Matplotlib para usar o motor do PyQt6 antes de renderizar os gráficos
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class DashboardEnergia(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bancada Trifásica - Monitoramento")
        self.setGeometry(100, 100, 1360, 760) # Ajustado levemente para acomodar os novos gráficos
        
        # Widget Central e Layout Principal (Fundo Cinza Escuro Antracite)
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #1E1E1E;")
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # ---------------------------------------------------------------------
        # CABEÇALHO (Base Cinza e Título Centralizado em Verde)
        # ---------------------------------------------------------------------
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #2B2B2B; border-radius: 8px;")
        header_frame.setFixedHeight(70)
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("Sistema de Monitoramento Inteligente de Energia Elétrica")
        title_label.setFont(QFont("Helvetica", 20, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2ECC71;") 
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label)
        
        main_layout.addWidget(header_frame)

        # Container do Conteúdo (Dividido em duas colunas)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # ---------------------------------------------------------------------
        # PAINEL DA ESQUERDA - VALORES ATUAIS (CARDS DE MEDIÇÃO)
        # ---------------------------------------------------------------------
        left_panel = QFrame()
        left_panel.setStyleSheet("background-color: #2B2B2B; border-radius: 12px;")
        left_panel.setFixedWidth(380)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)
        
        panel_title = QLabel("MEDIÇÃO INSTANTÂNEA")
        panel_title.setFont(QFont("Helvetica", 13, QFont.Weight.Bold))
        panel_title.setStyleSheet("color: #E0E0E0;")
        panel_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(panel_title)
        
        # Dicionário para armazenar as referências dos labels de cada fase
        self.cards = {}
        
        for fase in [1, 2, 3]:
            f_frame = QFrame()
            f_frame.setStyleSheet("background-color: #333333; border-radius: 8px; border: 1px solid #444444;")
            f_layout = QGridLayout(f_frame)
            f_layout.setContentsMargins(12, 10, 12, 10)
            
            f_title = QLabel(f"Fase {fase}")
            f_title.setFont(QFont("Helvetica", 11, QFont.Weight.Bold))
            f_title.setStyleSheet("color: #2ECC71; border: none;")
            f_layout.addWidget(f_title, 0, 0, 1, 2)
            
            lbl_p = QLabel("P. Ativa: -- W")
            lbl_p.setStyleSheet("color: #FFFFFF; border: none;")
            lbl_p.setFont(QFont("Helvetica", 10))
            f_layout.addWidget(lbl_p, 1, 0)
            
            lbl_q = QLabel("P. Reativa: -- VAr")
            lbl_q.setStyleSheet("color: #FFFFFF; border: none;")
            lbl_q.setFont(QFont("Helvetica", 10))
            f_layout.addWidget(lbl_q, 1, 1)
            
            lbl_s = QLabel("P. Aparente: -- VA")
            lbl_s.setStyleSheet("color: #FFFFFF; border: none;")
            lbl_s.setFont(QFont("Helvetica", 10))
            f_layout.addWidget(lbl_s, 2, 0)
            
            lbl_fp = QLabel("Fator de Pot.: --")
            lbl_fp.setStyleSheet("color: #2ECC71; border: none;") # Destaca o FP em verde
            lbl_fp.setFont(QFont("Helvetica", 10, QFont.Weight.Bold))
            f_layout.addWidget(lbl_fp, 2, 1)
            
            lbl_v = QLabel("Tensão: -- V")
            lbl_v.setStyleSheet("color: #B0B0B0; border: none;")
            lbl_v.setFont(QFont("Helvetica", 9))
            f_layout.addWidget(lbl_v, 3, 0)
            
            lbl_i = QLabel("Corrente: -- A")
            lbl_i.setStyleSheet("color: #B0B0B0; border: none;")
            lbl_i.setFont(QFont("Helvetica", 9))
            f_layout.addWidget(lbl_i, 3, 1)
            
            left_layout.addWidget(f_frame)
            self.cards[fase] = {"p": lbl_p, "q": lbl_q, "s": lbl_s, "fp": lbl_fp, "v": lbl_v, "i": lbl_i}
            
        left_layout.addStretch()
        content_layout.addWidget(left_panel)

        # ---------------------------------------------------------------------
        # PAINEL DA DIREITA - 3 GRÁFICOS DE POTÊNCIA EM TEMPO REAL
        # ---------------------------------------------------------------------
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: #2B2B2B; border-radius: 12px;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        # Cria matriz de 3 subplots verticais compartilhando o mesmo eixo X temporal
        self.fig, (self.ax_p, self.ax_q, self.ax_s) = plt.subplots(3, 1, figsize=(6, 6), sharex=True)
        self.fig.patch.set_facecolor('#2B2B2B')
        
        self.canvas = FigureCanvas(self.fig)
        right_layout.addWidget(self.canvas)
        
        content_layout.addWidget(right_panel)
        main_layout.addLayout(content_layout)

        # Configura o Timer para atualizar o Dashboard a cada 1000ms (1 segundo)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(1000)

    def update_dashboard(self):
        try:
            conn = sqlite3.connect("telemetria.db")
            df = pd.read_sql_query("SELECT * FROM leituras ORDER BY id DESC LIMIT 30", conn)
            conn.close()

            if not df.empty:
                df = df.iloc[::-1].reset_index(drop=True)
                
                # Trata as strings de data/hora para extrair APENAS 'HH:MM:SS'
                timestamps_formatados = []
                for ts in df['timestamp']:
                    try:
                        hora_pura = ts.split(" ")[1]
                        timestamps_formatados.append(hora_pura)
                    except Exception:
                        timestamps_formatados.append(ts)

                # Atualização dinâmica dos Cards textuais da esquerda
                atual = df.iloc[-1]
                for f in [1, 2, 3]:
                    self.cards[f]["p"].setText(f"P. Ativa: {atual[f'pr{f}']:.1f} W")
                    self.cards[f]["q"].setText(f"P. Reativa: {atual[f'qr{f}']:.1f} VAr")
                    self.cards[f]["s"].setText(f"P. Aparente: {atual[f'sr{f}']:.1f} VA")
                    self.cards[f]["fp"].setText(f"Fator de Pot.: {atual[f'fp{f}']:.3f}")
                    self.cards[f]["v"].setText(f"Tensão: {atual[f'tr{f}']:.1f} V")
                    self.cards[f]["i"].setText(f"Corrente: {atual[f'cr{f}']:.2f} A")

                # Limpa as plotagens antigas para reconstruir os eixos de forma limpa
                self.ax_p.clear()
                self.ax_q.clear()
                self.ax_s.clear()

                # Paleta de alta visibilidade industrial (Ciano, Magenta, Amarelo)
                cores_fases = {1: "#00FFFF", 2: "#FF00FF", 3: "#FFFF00"}
                indices = range(len(df))

                # Plotagem das 3 potências para cada fase
                for f in [1, 2, 3]:
                    # Gráfico 1: Potência Ativa (W)
                    self.ax_p.plot(indices, df[f'pr{f}'], color=cores_fases[f], linewidth=2, label=f"Fase {f}")
                    # Gráfico 2: Potência Reativa (VAr)
                    self.ax_q.plot(indices, df[f'qr{f}'], color=cores_fases[f], linewidth=2)
                    # Gráfico 3: Potência Aparente (VA)
                    self.ax_s.plot(indices, df[f'sr{f}'], color=cores_fases[f], linewidth=2)

                # --- Estilização do Gráfico 1: Potência Ativa (Superior) ---
                self.ax_p.set_title("Curva de Potência Ativa (W)", color="#FFFFFF", fontsize=10, loc="left")
                self.ax_p.set_facecolor('#1E1E1E')
                self.ax_p.tick_params(colors='#B0B0B0', labelsize=8, labelbottom=False)
                self.ax_p.grid(True, color="#444444", linestyle="--")
                self.ax_p.legend(facecolor='#2B2B2B', edgecolor='none', labelcolor='#FFFFFF', loc='upper left', fontsize=7)

                # --- Estilização do Gráfico 2: Potência Reativa (Central) ---
                self.ax_q.set_title("Curva de Potência Reativa (VAr)", color="#FFFFFF", fontsize=10, loc="left")
                self.ax_q.set_facecolor('#1E1E1E')
                self.ax_q.tick_params(colors='#B0B0B0', labelsize=8, labelbottom=False)
                self.ax_q.grid(True, color="#444444", linestyle="--")

                # --- Estilização do Gráfico 3: Potência Aparente (Inferior) ---
                self.ax_s.set_title("Curva de Potência Aparente (VA)", color="#FFFFFF", fontsize=10, loc="left")
                self.ax_s.set_facecolor('#1E1E1E')
                self.ax_s.tick_params(colors='#B0B0B0', labelsize=8)
                self.ax_s.grid(True, color="#444444", linestyle="--")

                # Filtro de densidade para as labels do único eixo X visível (o inferior)
                total_pontos = len(df)
                if total_pontos <= 5:
                    passos = 1  
                elif total_pontos <= 15:
                    passos = 2  
                else:
                    passos = 5  

                ticks_selecionados = list(range(0, total_pontos, passos))
                labels_selecionadas = [timestamps_formatados[i] for i in ticks_selecionados]

                self.ax_s.set_xticks(ticks_selecionados)
                self.ax_s.set_xticklabels(labels_selecionadas, rotation=0, ha="center")
                
                # Força todas as linhas a colarem perfeitamente nos cantos esquerdo e direito
                if total_pontos > 1:
                    self.ax_p.set_xlim(0, total_pontos - 1)
                    self.ax_q.set_xlim(0, total_pontos - 1)
                    self.ax_s.set_xlim(0, total_pontos - 1)

                self.fig.tight_layout()
                self.canvas.draw()

        except Exception as e:
            print(f"Erro na renderização dinâmica: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = DashboardEnergia()
    dashboard.show()
    sys.exit(app.exec())