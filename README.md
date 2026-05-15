# Especificação da Task de Processamento de Áudio

## Time 3.1 - Oficina de Desenvolvimento de Software

---

# 1. Objetivos

## Objetivos Gerais

Desenvolver um módulo de processamento de áudio em alto nível para a plataforma ESP32-P4, capaz de transformar sinais sonoros brutos em metadados claros e de fácil utilização, provendo uma interface simplificada e desacoplada para a camada de aplicação.

---

## Objetivos Específicos

### Padronização do Processamento de Sinal

- Configurar a cadeia de áudio para operar dentro de um padrão de amostragem, resolução e comunicação, garantindo escalabilidade e compatibilidade com futuras atualizações.
- Estabelecer um fluxo de dados eficiente entre as tasks de captação e processamento utilizando mecanismos de comunicação do FreeRTOS.

### Escalabilidade

- Estruturar o código de forma modular para permitir a inclusão futura de recursos de Machine Learning, como reconhecimento de comandos de voz, sem necessidade de reestruturação da arquitetura base.

### Algoritmos de Análise Dinâmica

- Implementar o cálculo de valor eficaz (RMS) para monitoramento contínuo do nível de ruído ambiente.
- Desenvolver lógica de detecção de transientes acústicos para identificação de variações súbitas e picos de amplitude no sinal.

### Abstração via API

- Criar uma interface de programação que exponha apenas os resultados do processamento (metadados), eliminando a necessidade de manipulação de buffers de áudio pelas camadas superiores do projeto.

---

# 2. Tecnologias Utilizadas

O software será executado no módulo **ESP32-P4**, utilizando o **FreeRTOS** como sistema operacional principal da plataforma.

O desenvolvimento será realizado em **C++** utilizando o framework oficial da Espressif, o **ESP-IDF**.

Para testes e simulações será utilizado o **Wokwi**, integrado ao ambiente **Visual Studio Code**.

O controle de versão será realizado utilizando **Git** e hospedagem em repositório no **GitHub**.

## Ferramentas

- ESP32-P4
- FreeRTOS
- ESP-IDF
- C++
- Wokwi
- Visual Studio Code
- Git
- GitHub

---

# 3. Arquitetura e Fluxo de Dados

A arquitetura utiliza um buffer compartilhado entre as tasks de captação e processamento de áudio.

O mecanismo escolhido para comunicação entre tasks é o **Stream Buffer** do FreeRTOS, ideal para fluxo contínuo de dados entre produtor e consumidor.

Essa abordagem mantém os sistemas desacoplados, facilitando:

- Escalabilidade
- Modularidade
- Flexibilidade de manutenção
- Evolução futura do sistema

---

## Configuração de Áudio

Os parâmetros foram definidos considerando:

- Limitações de memória e processamento do hardware
- Compatibilidade com bibliotecas avançadas de áudio e IA

### Parâmetros definidos

| Parâmetro              | Valor |
|------------------------|--------|
| Taxa de amostragem     | 16 kHz |
| Resolução              | 16 bits |
| Janela de leitura      | 20 ms |

---

## Metadados Gerados

Inicialmente, a API fornecerá:

- Detecção de variações abruptas de amplitude
- Nível de ruído ambiente

---

## Fluxo Simplificado

```text
Task de Captação (Produtor)
            ↓
      Stream Buffer
        (FreeRTOS)
            ↓
Task de Processamento (Consumidor)
            ↓
      API de Metadados
