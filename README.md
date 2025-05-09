# 🤖 Texta AI

Um assistente de texto inteligente que funciona em segundo plano, ativado por um atalho de teclado, com feedback visual moderno.

## 📖 Sobre o Projeto

O Texta AI é uma ferramenta de produtividade que:

1. Monitora uma tecla de atalho configurável (padrão: `Ctrl+Alt+C`)
2. Ao ser ativada com texto selecionado, captura o texto
3. Exibe uma animação visual moderna durante o processamento
4. Envia para uma LLM (OpenAI GPT) para correção gramatical e ortográfica
5. Cola o texto corrigido de volta, substituindo o original

A ferramenta funciona em qualquer aplicativo onde você possa selecionar e colar texto, tornando o processo de correção de texto mais rápido e eficiente.

### ✨ Características

- **Interface Visual Moderna**: Animação minimalista com efeitos de pulso, gradientes e partículas
- **Feedback em Tempo Real**: A animação segue o cursor e indica o status do processamento
- **Sistema Robusto**: Tratamento avançado de erros com retentativas automáticas
- **Alta Confiabilidade**: Cobertura de testes de 87% e validação extensiva
- **Configurável**: Tecla de atalho e prompt de correção personalizáveis
- **Logging Detalhado**: Sistema completo de logs para console e arquivo

## 🛠️ Requisitos

- Python 3.9 ou superior
- Chave de API da OpenAI
- Bibliotecas Python (instaladas automaticamente pelo `pip`)
- Sistema operacional: Windows (testado no Windows 10)

## 📥 Instalação

1. **Clone o Repositório**
   ```bash
   git clone https://github.com/seu-usuario/texta-ai.git
   cd texta-ai
   ```

2. **Configure o Ambiente Virtual**
   
   É altamente recomendado usar um ambiente virtual para isolar as dependências do projeto.

   No Windows:
   ```bash
   # Criar ambiente virtual
   python -m venv .venv
   
   # Ativar ambiente virtual
   .venv\Scripts\activate
   ```

   No Linux/Mac:
   ```bash
   # Criar ambiente virtual
   python -m venv .venv
   
   # Ativar ambiente virtual
   source .venv/bin/activate
   ```

3. **Instale as Dependências**
   ```bash
   # Atualizar pip para a última versão
   python -m pip install --upgrade pip
   
   # Instalar dependências do projeto
   pip install -r requirements.txt
   ```

4. **Configure o Arquivo .env**
   
   Crie um arquivo `.env` na raiz do projeto com as seguintes configurações:
   ```env
   # Sua chave de API da OpenAI (obrigatória)
   OPENAI_API_KEY=sua_chave_api_aqui
   
   # Tecla de atalho (opcional, padrão: ctrl+alt+c)
   HOTKEY=ctrl+alt+c
   
   # Prompt de correção (opcional)
   CORRECTION_PROMPT=Você é um assistente especialista em correção de texto em português brasileiro. Sua tarefa é corrigir a gramática, ortografia e pontuação do texto fornecido. Mantenha o significado original e o tom/estilo do texto o máximo possível. Responda APENAS com o texto corrigido, sem adicionar introduções, saudações, despedidas, explicações ou comentários adicionais. Se o texto de entrada já estiver correto, retorne o texto original sem modificações. Texto a ser corrigido:
   ```

5. **Verificação da Instalação**
   ```bash
   # Verifique se o Python está correto
   python --version  # Deve mostrar 3.9 ou superior
   
   # Verifique se as dependências foram instaladas
   pip list  # Deve mostrar todas as bibliotecas necessárias
   ```

## 🚀 Uso

1. Execute o programa:
   ```bash
   python src/main.py
   ```

2. A aplicação iniciará e ficará monitorando a tecla de atalho configurada no arquivo `.env` (padrão: `Ctrl+Alt+C`).

3. Para corrigir um texto:
   - Selecione o texto em qualquer aplicativo
   - Pressione a tecla de atalho (padrão: `Ctrl+Alt+C`)
   - Uma animação visual aparecerá próxima ao cursor indicando o processamento
   - O texto será capturado, enviado para correção e o texto corrigido será colado de volta

4. Para encerrar o programa, pressione `Ctrl+C` no terminal onde o programa está sendo executado.

## ⚙️ Configuração

Você pode personalizar as seguintes configurações no arquivo `.env`:

- `OPENAI_API_KEY`: Sua chave de API da OpenAI (obrigatória)
- `HOTKEY`: A tecla de atalho para ativar a correção (padrão: `ctrl+alt+c`)
- `CORRECTION_PROMPT`: O prompt que será enviado para a LLM junto com o texto a ser corrigido

## 📝 Sistema de Logging

A aplicação mantém registros detalhados da execução:

- Os logs são exibidos no console durante a execução
- Todos os logs também são salvos no arquivo `logs/texta-ai.log`
- Diferentes níveis de log são utilizados (INFO, WARNING, ERROR, DEBUG)
- O formato dos logs inclui timestamp, nome do módulo, nível e mensagem
- A pasta `logs` é criada automaticamente na primeira execução

## ❌ Tratamento de Erros

O Texta AI inclui um sistema robusto de tratamento de erros:

- **Retentativas Automáticas**: Em caso de falhas temporárias de rede ou serviço
- **Backoff Exponencial**: Espera inteligente entre tentativas para evitar sobrecarga
- **Mensagens Claras**: Feedback específico sobre o tipo de erro encontrado
- **Categorização de Erros**: Tratamento específico para diferentes tipos de falha:
  - Problemas de conexão
  - Timeouts
  - Erros de autenticação
  - Limites de taxa (rate limits)
  - Indisponibilidade do serviço

## 🔍 Solução de Problemas

Se a ferramenta não estiver funcionando como esperado:

1. Certifique-se de que o texto está selecionado antes de pressionar a tecla de atalho
2. Algumas aplicações podem restringir a funcionalidade de copiar/colar
3. Tente executar o script sem privilégios administrativos
4. Verifique o terminal ou o arquivo de log `logs/texta-ai.log` para mensagens de erro
5. Em caso de erros de rede, a aplicação tentará automaticamente algumas vezes antes de desistir
6. Se a animação visual não aparecer, verifique se sua placa gráfica suporta aceleração de hardware

## 📊 Status do Projeto

- **Versão Atual**: 1.0.0
- **Cobertura de Testes**: 87%
- **Testes Unitários**: 33 testes implementados e passando
- **Estado**: Estável, em fase de testes de confiabilidade

## 🧪 Executando os Testes

Para executar os testes unitários e verificar a cobertura de código:

```bash
# Executar todos os testes com relatório de cobertura
pytest --cov=src tests/

# Executar testes com relatório detalhado de cobertura
pytest --cov=src --cov-report=term-missing tests/

# Executar testes de um módulo específico
pytest tests/test_capture.py

# Executar testes com saída detalhada
pytest -v tests/
```

O relatório de cobertura mostrará a porcentagem de código coberto por testes para cada módulo em `src/`.

## 📄 Licença

Este projeto é licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

## 👥 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests. 