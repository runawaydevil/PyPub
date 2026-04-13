# Troubleshooting

Se você está batendo cabeça contra a parede, acesse isso:

### 0. Executável empacotado (PyInstaller) não abre, fecha logo ou erro de Shiboken / Qt

- **UPX:** o projeto usa `upx=False` no [pypub.spec](../pypub.spec). Se alterou e voltou a ativar UPX, desative — compressão UPX quebra frequentemente DLLs Qt.
- **Hooks:** mantenha `pyinstaller` e `pyinstaller-hooks-contrib` atualizados (`pip install -U pyinstaller pyinstaller-hooks-contrib` no mesmo venv de build).
- **WebEngine / OAuth:** o login embutido usa `QWebEngineView`. Confirme que existem `QtWebEngineProcess.exe`, ficheiros `.pak` e o plugin `platforms\qwindows.dll` dentro de `dist\PyPub\` — rode `.\scripts\verify-frozen-bundle.ps1 -BundlePath dist\PyPub`.
- **Consola de diagnóstico:** defina `PYPUB_PYI_CONSOLE=1` e gere `PyPub_console.exe` (ver [BUILD.md](BUILD.md)) para ver `ImportError` ou falhas na arranque.
- **Sandbox (só teste):** se suspeitar do processo Chromium, experimente temporariamente `QTWEBENGINE_DISABLE_SANDBOX=1` ao lançar o `.exe` (não recomendado para produção).
- **Visual C++ Redistributable:** o wheel do PySide6 precisa dos **VC++ Redistributables** x64 instalados na máquina alvo (instalador típico Microsoft). Sem eles, o processo pode falhar ao carregar DLLs sem mensagem útil em modo janela.

### 1. O Endpoint Micropub não foi descoberto no login ("Endpoint Not Found")
Verifique o HTML Head da aba da sua homepage principal (`Ver Código-Fonte`), devem existir:
`<link rel="micropub" href="...">`

### 2. Ao usar PKCE pra login, o Browser diz "Connection Refused / Can't connect to Localhost"
Isso acorre se sua Firewall estiver bloqueando a porta interna 8080 durante os 15 segundos que o PyPub tenta esperar pelo Token de callback do Browser.
Vou no Defender -> Rules e autorize Python Local Socket.

### 3. Minhas Anotações Salvas (Drafts) Evaporaram e o app sumiu após um Update
As novas versões usam o `appdirs` para fixar arquivos persistentes no cofre de roaming de sua máquina Windows de forma imutável. Porém, em dias de corrupção massiva a database estará em:
`C:\Users\<Você>\AppData\Local\Pablo Murad\PyPub\pypub.sqlite`
Abra em qualquer DBViewer SQLite e veja a Table `drafts`. Seus textos brutos estarão salvos em Clear Text!

### 4. O Sistema fecha repentinamente (Crash Silencioso)
Vá à pasta supracitada, acesse o canal de Logs:
`C:\Users\<Você>\AppData\Local\Pablo Murad\PyPub\Logs\` e leia `pypub.log`. Uma Callstack rastreando a quebra em PyQt e Http estará documentada até a raiz.
