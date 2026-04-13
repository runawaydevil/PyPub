# Guia de Build - PyPub

Para compilar o PyPub do código fonte para um executável Windows, siga as premissas abaixo.

## Requisitos de Ambiente
* Windows 10 ou 11 (X64)
* Python 3.12+ (Download e marque a opção *Add to PATH*)
* Inno Setup 6+ (Opcional, apenas para gerar o Setup final encapsulado)

## Passos para Compilar

1. **Baixe o Código:**
   Faça o clone ou o download do zip deste repositório e abra o Terminal/PowerShell na pasta descompactada.

2. **Execute o Script de Build do Windows:**
   Nós empacotamos o pipeline todo via PowerShell. Basta rodar:
   ```powershell
   .\build.ps1
   ```

   **O que o Script faz:**
   - Instala o PyPub em modo local via `pip`.
   - Baixa e isola dependências (PyInstaller, Pytest).
   - Valida a branch ativa acionando o framework de testes.
   - Evoca o `PyInstaller` passando a instrução `pypub.spec` que coleta ganchos ocultos do SQLite e bibliotecas C de criptografia (nh3/markdown).
   
3. **Localize o Executável:**
   Ao final do processamento verde no console, abra a sub-pasta `dist/PyPub/`. Lá residem todas as dlls dependentes e o binário principal `PyPub.exe`.

4. **Gerando o Instalador (Opcional):**
   Para transformar a caótica pasta `dist` num belo `PyPub-Setup-0.0.1.exe`, baixe o programa *Inno Setup Compiler* da web. Clique no arquivo `installer.iss` localizado neste projeto. Clique em **Compile**. Ele despejará o instalador consolidado.
