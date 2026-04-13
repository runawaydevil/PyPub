# Guia de Build - PyPub

Para compilar o PyPub do código fonte para um executável Windows, siga as premissas abaixo.

## Requisitos de Ambiente
* Windows 10 ou 11 (X64)
* Python 3.12+ (Download e marque a opção *Add to PATH*)
* Inno Setup 6+ (Opcional, apenas para gerar o Setup final encapsulado)

**Dependências de empacotamento:** `pip install -e .[dev]` instala `pyinstaller`, `pyinstaller-hooks-contrib` (hooks para Qt/WebEngine) e testes. Mantenha o `pyinstaller-hooks-contrib` atualizado junto do PyInstaller se o bundle faltar DLLs ou o processo `QtWebEngineProcess`.

## Passos para Compilar

1. **Baixe o Código:**
   Faça o clone ou o download do zip deste repositório e abra o Terminal/PowerShell na pasta descompactada.

2. **Execute o Script de Build do Windows:**

   **Release (recomendado antes de distribuir):** instala dependências, roda testes, PyInstaller e verificação do bundle.
   ```powershell
   .\build.ps1
   ```

   **Iteração rápida** (sem `pip` nem `pytest`; use só com venv já correto):
   ```powershell
   .\build.ps1 -Fast
   ```
   Ou separado: `.\build.ps1 -SkipInstall`, `.\build.ps1 -SkipTests`, ou ambos.

   **O que o Script faz (modo completo):**
   - Instala o PyPub em modo local via `pip` (opcional com `-SkipInstall` / `-Fast`).
   - Roda `pytest` (opcional com `-SkipTests` / `-Fast`).
   - Evoca o `PyInstaller` com [pypub.spec](../pypub.spec) (**UPX desativado** — compressão UPX costuma quebrar Qt/Shiboken/WebEngine).
   - Executa [scripts/verify-frozen-bundle.ps1](../scripts/verify-frozen-bundle.ps1) no bundle em staging (QtWebEngineProcess, `.pak`, plugin `qwindows`, etc.).
   - Smoke-test do executável e promoção para `dist\PyPub`.

3. **Localize o Executável:**
   Ao final do processamento verde no console, abra a sub-pasta `dist/PyPub/`. Lá residem todas as dlls dependentes e o binário principal `PyPub.exe`.

4. **Verificação manual do bundle (após build):**
   ```powershell
   .\scripts\verify-frozen-bundle.ps1 -BundlePath dist\PyPub
   ```

5. **Build com consola para diagnóstico (erros no terminal):**
   O [pypub.spec](../pypub.spec) gera `PyPub.exe` sem consola por defeito. Para ver tracebacks ao iniciar:
   ```powershell
   $env:PYPUB_PYI_CONSOLE = "1"
   python -m PyInstaller --noconfirm --distpath dist_stage --workpath build_stage pypub.spec
   ```
   O resultado fica em `dist_stage\PyPub_console\PyPub_console.exe`. Remova a variável para voltar ao modo janela:
   `Remove-Item Env:PYPUB_PYI_CONSOLE`

6. **Gerando o Instalador (Opcional):**
   Para transformar a pasta `dist` num `PyPub-Setup-<versão>.exe`, use o *Inno Setup Compiler* no [installer.iss](../installer.iss) e **Compile**. O script de build atualiza `AppVersion` e `OutputBaseFilename` a partir de `src/pypub/__init__.py`.
