import sqlite3
import json
import paho.mqtt.client as mqtt
from datetime import datetime
import ssl

# =============================================================================
# SELEÇÃO DO MODO DE TRANSPORTE E SEGURANÇA (IDÊNTICO AO SEU ESP32)
# Defina como 0: Modo convencional (Porta 1844, Usuário/Senha, Sem Criptografia)
# Defina como 1: Modo avançado industrial (Porta 8844, TLS-PSK Criptografado)
# =============================================================================
USE_MQTT_TLS_PSK = 1

DB_NAME = "telemetria.db"
BROKER_IP = "192.168.0.9"

if USE_MQTT_TLS_PSK == 1:
    BROKER_PORT = 8844
    PSK_IDENTITY = "isac"
    PSK_KEY_HEX  = "ABCD44EF12345678"
else:
    BROKER_PORT = 1844
    USERNAME = "isac"
    PASSWORD = "isac"

TOPIC = "casa/temp"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            tr1 REAL, cr1 REAL, pr1 REAL, qr1 REAL, sr1 REAL, fp1 REAL,
            tr2 REAL, cr2 REAL, pr2 REAL, qr2 REAL, sr2 REAL, fp2 REAL,
            tr3 REAL, cr3 REAL, pr3 REAL, qr3 REAL, sr3 REAL, fp3 REAL
        )
    ''')
    conn.commit()
    conn.close()

def on_connect(client, userdata, flags, rc, properties=None):
    # Ajustado assinatura para suportar os parâmetros de propriedades do Paho v2
    if rc == 0:
        print(f" Conectado com sucesso ao Broker {BROKER_IP} na porta {BROKER_PORT}!")
        client.subscribe(TOPIC)
        print(f" Escutando e gravando dados do tópico: '{TOPIC}'...")
    else:
        print(f"❌ Falha na conexão. Código de retorno do Broker: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO leituras (
                timestamp, 
                tr1, cr1, pr1, qr1, sr1, fp1,
                tr2, cr2, pr2, qr2, sr2, fp2,
                tr3, cr3, pr3, qr3, sr3, fp3
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            now,
            payload.get('tr1', 0), payload.get('cr1', 0), payload.get('pr1', 0), payload.get('qr1', 0), payload.get('sr1', 0), payload.get('fp1', 0),
            payload.get('tr2', 0), payload.get('cr2', 0), payload.get('pr2', 0), payload.get('qr2', 0), payload.get('sr2', 0), payload.get('fp2', 0),
            payload.get('tr3', 0), payload.get('cr3', 0), payload.get('pr3', 0), payload.get('qr3', 0), payload.get('sr3', 0), payload.get('fp3', 0)
        ))
        conn.commit()
        conn.close()
        print(f"[{now}] 💾 Telemetria Trifásica salva com sucesso no SQLite.")
    except Exception as e:
        print(f"⚠️ Erro ao processar string JSON ou gravar no banco: {e}")

if __name__ == "__main__":
    init_db()
    
    # Inicializa a API do cliente Paho MQTT estruturada para a versão 2.x
    from paho.mqtt.enums import CallbackAPIVersion
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    # -------------------------------------------------------------------------
    # CONFIGURAÇÃO DE SEGURANÇA SELECIONADA
    # -------------------------------------------------------------------------
    if USE_MQTT_TLS_PSK == 1:
        print("🔒 Inicializando conexão criptografada via TLS-PSK (Porta 8844)...")
        
        # 1. Instancia um contexto TLS limpo e seguro para rodar em modo cliente
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # 2. Configura a lista de cifras aceitas pelo OpenSSL do Debian para focar em PSK
        context.set_ciphers('PSK')
        
        # 3. Mapeia a função de callback nativa do OpenSSL. Sempre que o Mosquitto pedir 
        # as credenciais simétricas no handshake, o socket responde de forma transparente.
        psk_bytes = bytes.fromhex(PSK_KEY_HEX)
        context.set_psk_client_callback(lambda hint: (PSK_IDENTITY, psk_bytes))
        
        # 4. Vincula o contexto nativo e seguro ao cliente do Paho MQTT de forma limpa
        client.tls_set_context(context)
        client.tls_insecure_set(True)
        
    else:
        print("🔓 Inicializando conexão padrão via TCP plano (Porta 1844)...")
        client.username_pw_set(USERNAME, PASSWORD)
    
    # Conecta ao endereço IP do computador e inicia o loop infinito
    client.connect(BROKER_IP, BROKER_PORT, 60)
    client.loop_forever()