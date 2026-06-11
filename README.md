

# # Sistema de Monitoramento Inteligente de Energia Elétrica (Bancada Trifásica)

Este repositório contém a infraestrutura de software de alto nível para um **Sistema de Monitoramento e Telemetria de Grandezas Elétricas em Ambientes Trifásicos**. Desenvolvido como parte de um Trabalho de Conclusão de Curso (TCC), o ecossistema realiza a ingestão, persistência e visualização gráfica em tempo real de dados metrológicos provenientes de um nó sensor remoto (ESP32).

---

## 🚀 Características do Sistema

* **Segurança Industrial (TLS-PSK):** Transporte de dados criptografado de ponta a ponta via hardware (MQTTS) utilizando chaves simétricas pré-compartilhadas na porta `8844`, eliminando a necessidade de infraestruturas complexas de PKI (certificados).
* **Ingestão Assíncrona:** Serviço de background otimizado para a API do Paho-MQTT 2.x, garantindo estabilidade no recebimento de payloads estruturados em JSON.
* **Persistência Confiável:** Armazenamento local permanente utilizando SQLite, mantendo a integridade metrológica dos dados sem perda de precisão por arredondamento.
* **Interface Gráfica de Alto Nível:** Dashboard desenvolvido inteiramente em PyQt6 com backend gráfico `QtAgg`, proporcionando visualização fluida e independente de dependências gráficas do sistema operacional.

---

## 📁 Estrutura do Repositório

```text
├── logger.py          # Serviço de escuta MQTT e gravação no banco de dados
├── dashboard.py       # Interface gráfica e plotagem dinâmica em tempo real
├── telemetria.db      # Banco de dados SQLite gerado automaticamente
└── README.md          # Documentação do projeto

```

* **`logger.py`**: Conecta-se ao Broker MQTT Mosquitto via TLS-PSK, intercepta os payloads das três fases no tópico configurado, valida a integridade e insere os registros na base SQLite.
* **`dashboard.py`**: Aplicação visual que consome a base de dados a cada 1 segundo, atualizando cartões textuais de medição instantânea e renderizando 3 subplots empilhados (Potência Ativa, Reativa e Aparente) divididos por fases.

---

## 🛠️ Stack Tecnológica e Pré-requisitos

O sistema foi homologado e validado no seguinte ambiente de desenvolvimento:

* **Sistema Operacional:** Linux (Debian 13 Trixie / Ubuntu)
* **Interpretador:** Python 3.13.5
* **Broker:** Eclipse Mosquitto (Configurado com suporte a TLS-PSK)

### Dependências do Python

* `paho-mqtt` (v2.x)
* `PyQt6`
* `matplotlib`
* `pandas`

---

## 🔧 Instalação e Configuração

Devido às diretivas de ambientes gerenciados externamente (PEP 668), é obrigatório o uso de um ambiente virtual (`venv`) para isolar as dependências do projeto.

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/nome-do-repositorio.git
cd nome-do-repositorio

```



```

2. **Crie e ative o ambiente virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate

```

3. **Atualize o gerenciador de pacotes interno:**
```bash

```



pip install --upgrade pip

```

4. **Instale as dependências requeridas:**
   ```bash
pip install paho-mqtt PyQt6 matplotlib pandas

```

---

## 🕹️ Como Executar o Sistema

O funcionamento do ecossistema exige a execução combinada de dois terminais (ambos com o ambiente virtual ativado).

### Passo 1: Iniciar o Logger (Ingestão)

Abra um terminal, ative o `venv` e execute o script de escuta. **Nota:** Não utilize privilégios de superusuário (`sudo`), pois o script roda inteiramente em espaço de usuário local.

```bash
source venv/bin/activate
python3 logger.py

```

*Esperado no terminal:*

> 🔒 Inicializando conexão criptografada via TLS-PSK (Porta 8844)...
> Conectado com sucesso ao Broker!
> Escutando e gravando dados...

### Passo 2: Iniciar o Dashboard (Visualização)

Abra um segundo terminal, ative o `venv` e chame a interface gráfica:

```bash
source venv/bin/activate
python3 dashboard.py

```

---

## 📊 Modelagem dos Dados (SQLite)

Os dados são armazenados na tabela `leituras` no arquivo `telemetria.db` com dupla precisão (`REAL`), estruturados conforme o mapeamento abaixo:

| Coluna | Tipo | Descrição |
| --- | --- | --- |
| `id` | INTEGER | Chave primária com autoincremento |
| `timestamp` | TEXT | Carimbo de data/hora no padrão ISO 8601 (`AAAA-MM-DD HH:MM:SS`) |
| `tr1`, `tr2`, `tr3` | REAL | Tensão eficaz (RMS) das Fases 1, 2 e 3 (V) |
| `cr1`, `cr2`, `cr3` | REAL | Corrente eficaz (RMS) das Fases 1, 2 e 3 (A) |
| `pr1`, `pr2`, `pr3` | REAL | Potência Ativa das Fases 1, 2 e 3 (W) |
| `qr1`, `qr2`, `qr3` | REAL | Potência Reativa das Fases 1, 2 e 3 (VAr) |
| `sr1`, `sr2`, `sr3` | REAL | Potência Aparente das Fases 1, 2 e 3 (VA) |
| `fp1`, `fp2`, `fp3` | REAL | Fator de Potência das Fases 1, 2 e 3 (Adimensional de 0.000 a 1.000) |

---

## 🎨 Identidade Visual Industrial

A interface gráfica adota uma paleta de cores escura em tom antracite (`#1E1E1E` / `#2B2B2B`) com alto contraste para reduzir a fadiga ocular em ambientes de laboratório ou salas de controle.

As curvas temporais seguem estritamente a padronização metrológica por cores de alta visibilidade:

* 🟦 **Fase 1:** Ciano (`#00FFFF`)
* 🟪 **Fase 2:** Magenta (`#FF00FF`)
* 🟨 **Fase 3:** Amarelo (`#FFFF00`)
