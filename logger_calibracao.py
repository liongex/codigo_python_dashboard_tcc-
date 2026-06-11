import sqlite3
import json
import paho.mqtt.client as mqtt
from datetime import datetime

# Configurações Macrossociais do seu Ambiente de Calibração
MQTT_BROKER = "192.168.0.9"
MQTT_PORT = 1844
MQTT_USER = "isac"
# Certifique-se de que a senha está correta
MQTT_PASS = "isac" 

TOPIC_AMOSTRAS = "casa/dados"
DB_NAME = "bancada_amostras.db"

# 🗄️ CRIAÇÃO EXCLUSIVA DO BANCO DE DADOS DE FORMAS DE ONDA
def init_calibration_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ondas_trifasicas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ponto INTEGER,
            v1 REAL, v2 REAL, v3 REAL,
            i1 REAL, i2 REAL, i3 REAL
        )
    """)
    conn.commit()
    conn.close()
    print(f"Banco de dados '{DB_NAME}' verificado/inicializado com sucesso.")

# 📩 RECEPTOR E DESTRUTURADOR DOS ARRAYS TRIFÁSICOS
def on_message(client, userdata, msg):
    # Carimbo temporal com precisão de milisegundos para sincronia metrológica posterior
    timestamp_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    try:
        if msg.topic == TOPIC_AMOSTRAS:
            payload = json.loads(msg.payload.decode())
            
            v1, v2, v3 = payload.get("v1", []), payload.get("v2", []), payload.get("v3", [])
            i1, i2, i3 = payload.get("i1", []), payload.get("i2", []), payload.get("i3", [])
            
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            
            # Monta o lote sequencial paralelo das 3 fases para inserção atômica veloz
            lote_amostras = []
            for idx in range(100):
                lote_amostras.append((
                    timestamp_atual, idx,
                    v1[idx] if idx < len(v1) else 0.0,
                    v2[idx] if idx < len(v2) else 0.0,
                    v3[idx] if idx < len(v3) else 0.0,
                    i1[idx] if idx < len(i1) else 0.0,
                    i2[idx] if idx < len(i2) else 0.0,
                    i3[idx] if idx < len(i3) else 0.0
                ))
            
            # Insere o bloco inteiro de uma vez para proteger o desempenho do SD/HD do Debian
            cursor.executemany("""
                INSERT INTO ondas_trifasicas (timestamp, ponto, v1, v2, v3, i1, i2, i3)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, lote_amostras)
            
            conn.commit()
            conn.close()
            print(f"[{timestamp_atual}] Lote de Calibracao: 100 pontos trifasicos armazenados.")
            
    except Exception as e:
        print(f"Erro ao decodificar pacote de amostras: {e}")

# 🚀 INICIALIZADOR DO LOGGER DE CALIBRAÇÃO
def main():
    init_calibration_db()
    
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_message = on_message
    
    print(f"Conectando ao Broker de Coleta em {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    client.subscribe(TOPIC_AMOSTRAS, 0)
    
    print("Modo de Coleta Ativo. Aguardando rajadas de ondas da bancada... (Ctrl+C para sair)")
    client.loop_forever()

if __name__ == "__main__":
    main()