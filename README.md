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
- Chave de API da OpenAI (configurada em um arquivo `.env`)
- Poetry para gerenciamento de dependências e ambiente virtual
- Sistema operacional: Windows (testado no Windows 11)

## 📥 Configuração do Ambiente
1. **Clone o Repositório** (se ainda não o fez)
   ```bash
   git clone https://github.com/seu-usuario/texta-ai.git
   cd texta-ai
   ```

2. **Instale o Poetry** (se ainda não o tem)
   Poetry é o gerenciador de dependências e ambientes virtuais do projeto.
   ```powershell
   # Execute no PowerShell:
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
   ```
   Após a instalação, pode ser necessário reiniciar seu terminal ou adicionar o Poetry ao PATH.

3. **Configure o Poetry para criar o ambiente virtual no projeto**
   ```bash
   poetry config virtualenvs.in-project true
   ```

4. **Instale as Dependências do Projeto**
   ```bash
   # Isso instalará todas as dependências principais e de desenvolvimento
   poetry install --with dev
   ```

5. **Configure o Arquivo .env**
   
   Crie um arquivo `.env` na raiz do projeto copiando o arquivo de exemplo:
   ```bash
   # Windows (PowerShell)
   cp .env.example .env
   ```
   
   Em seguida, edite o arquivo `.env` e preencha com seus valores:
   ```env
   # Sua chave de API da OpenAI (obrigatória)
   OPENAI_API_KEY=sua_chave_api_aqui
   
   # Tecla de atalho (opcional, padrão: ctrl+alt+c)
   HOTKEY=ctrl+alt+c
   
   # Prompt de correção (opcional)
   CORRECTION_PROMPT=Você é um assistente especialista em correção de texto em português brasileiro. Sua tarefa é corrigir a gramática, ortografia e pontuação do texto fornecido. Mantenha o significado original e o tom/estilo do texto o máximo possível. Responda APENAS com o texto corrigido, sem adicionar introduções, saudações, despedidas, explicações ou comentários adicionais. Se o texto de entrada já estiver correto, retorne o texto original sem modificações. Texto a ser corrigido:
   ```

5. **Verificação da Instalação**
   Para verificar se tudo foi configurado corretamente:
   ```bash
   poetry run python --version # Deve mostrar 3.9 ou superior
   poetry run pytest --version # Deve mostrar a versão do pytest
   poetry run ruff --version   # Deve mostrar a versão do ruff
   ```

## 🚀 Uso

1. Execute o programa:
   ```bash
   # Isso executa o script usando o ambiente virtual gerenciado pelo Poetry
   poetry run python src/main.py
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

A aplicação utiliza a biblioteca `Loguru` para um sistema de logging detalhado e configurável:

- **Console Colorido:** Os logs exibidos no console são coloridos para fácil diferenciação de níveis (INFO, WARNING, ERROR) e módulos, com o formato: `[NÍVEL] MÓDULO: Mensagem`.
- **Arquivo de Log:** Todos os logs também são salvos no arquivo `logs/texta-ai.log` com o formato `[NÍVEL] MÓDULO: Mensagem` (sem cores) e com rotação de arquivo configurada para 10MB.
- **Níveis de Log:** Diferentes níveis de log são utilizados para granularidade (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
- **Configuração Centralizada:** A configuração do logger é gerenciada em `src/logger_config.py`.
- **Criação Automática de Pasta:** A pasta `logs/` é criada automaticamente se não existir.
- **Diagnóstico Aprimorado de Erros:** Os logs de arquivo incluem rastreamento detalhado de exceções com:
  - `backtrace=True`: Captura o traceback completo de exceções.
  - `diagnose=True`: Mostra os valores das variáveis nos diversos níveis do traceback, facilitando a identificação da causa raiz.

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
- **Cobertura de Testes**: 85%
- **Testes Unitários**: 59 testes implementados e passando
- **Estado**: Estável, em fase de testes de confiabilidade

## 🧪 Executando os Testes

Para executar a suíte completa de testes unitários e gerar um relatório de cobertura de código, utilize o seguinte comando:

```bash
poetry run pytest
```

Toda a configuração dos testes, incluindo a análise de cobertura, está centralizada no arquivo `pyproject.toml`. O comando acima é suficiente para validar todo o projeto.

O relatório de cobertura mostrará a porcentagem de código coberto por testes para cada módulo em `src/`.

## 📄 Licença

Este projeto é licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

## 👥 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests. 