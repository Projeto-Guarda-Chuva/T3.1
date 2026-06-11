# Processamento de Áudio e Reconhecimento de Comandos por Voz

Este repositório contém um sistema de reconhecimento de voz offline de alta performance e baixa latência, projetado especificamente para rodar em dispositivos embarcados e de borda (Edge Computing), como a **Nvidia Jetson**, utilizando sistemas baseados em Linux. 

A aplicação substitui soluções legadas em C por uma arquitetura moderna e totalmente desacoplada em Python 3, eliminando gargalos históricos de latência por meio de um pipeline de execução concorrente multi-threaded sincronizado com um servidor de mensageria assíncrono via WebSockets.

---

## 🏗️ Arquitetura do Sistema

Para alcançar processamento em tempo real sem perda de pacotes de áudio (*frame dropping*), a aplicação foi desenhada sob um modelo de concorrência que separa as responsabilidades de rede, buffering, inferência e saída em threads distintas:

```text
┌────────────────────────────────────────────┐
│           PcmBuffer                        │
└──────────────┬─────────────────────────────┘
               │
               ▼
             (Read)
┌────────────────────────────────────────────┐
│ AudioProcessorService (AI Inference Layer) │
└──────────────┬─────────────────────────────┘
               │
               ├──────────────► Neural Model (Vosk)
               │
               ▼
┌────────────────────────────────────────────┐
│    GatewayService (WebSocket Server)       │
└──────────────┬─────────────────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │ Web Clients / Applications   │
    └──────────────────────────────┘
```

# Instalação e Dependências

## Pré-requisitos

Antes de executar o projeto, certifique-se de que os seguintes requisitos estão instalados na máquina alvo:

| Requisito | Versão / Recomendação |
|---|---|
| Sistema Operacional | Linux (Ubuntu 20.04 LTS ou superior recomendado) |
| Python | Python 3.10+ |
---

# 1. Clonar e Acessar o Repositório

Navegue até o diretório onde o repositório foi clonado:

```bash
cd /home/nome-de-usuario/T3.1
```

---

# 2. Configurar o Ambiente Virtual Python

Crie um ambiente Python isolado e instale todas as dependências necessárias.

## Criar o ambiente virtual

```bash
python3 -m venv .venv
```

## Ativar o ambiente virtual

```bash
source .venv/bin/activate
```

## Atualizar o pip e instalar as dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

# 3. Baixar e Configurar o Modelo de Reconhecimento de Voz (Português)

O sistema utiliza um modelo acústico offline do Vosk para reconhecimento de fala.

Siga exatamente os comandos abaixo para baixar e configurar o modelo:

## Garantir que está na raiz do projeto

```bash
cd /home/nome-de-usuario/T3.1
```

## Criar o diretório de modelos

```bash
mkdir -p models
cd models
```

## Baixar o modelo compacto em português brasileiro

```bash
curl -O https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip
```

## Extrair os arquivos compactados

```bash
unzip vosk-model-small-pt-0.3.zip
```

## Remover o arquivo zip para liberar espaço em disco

```bash
rm vosk-model-small-pt-0.3.zip
```

## Retornar para a raiz do projeto

```bash
cd ..
```

---

# Executando o Sistema

A arquitetura segue um modelo cliente-servidor baseado em streaming.

O backend Python deve permanecer ativo para receber e processar o fluxo de áudio enviado pelo terminal de captura.

---

# Iniciar o Servidor Principal (Backend Python)

Com o ambiente virtual ativado, configure o `PYTHONPATH` e execute o serviço principal:

```bash
export PYTHONPATH=/home/nome-de-usuario/T3.1
python audio_processor/main.py
```

---

# Saída Esperada

Durante a inicialização, o console exibirá o processo de carregamento do modelo Vosk e confirmará que o gateway WebSocket está ativo e aguardando conexões:

```text
[GatewayService] Server actively listening on ws://0.0.0.0:9090
```

---

# Visão Geral do Sistema

O fluxo de execução é composto por:

1. Ingestão do áudio pelo backend Python
2. Reconhecimento de fala em tempo real utilizando Vosk
3. Broadcast de payloads JSON através de conexões WebSocket
