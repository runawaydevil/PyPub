# PyPub Architecture Overview

A base de código utiliza **Domain-Driven Design (DDD)** simplificado.

## Divisão de Diretórios
- `src/pypub/domain/` - O Core absoluto do sistema. Todos os Contratos e Dataclass (`Draft`, `Account`) sem conhecimento de frameworks de UI ou SQL. E Modos do Editor. Pydantic impõe regras firmes.
- `src/pypub/infrastructure/` - Fronteiras onde a terra toca.
  - `db.py`: Migrações estritas mapeadas no SQLite.
  - `indieauth.py`/`micropub.py`: HttpX puro implementando OAuth.
  - `keyring_store.py`: Abstração do Gerenciador de Senhas.
- `src/pypub/application/` - Maestros! `auth_service.py` injeta BD e Token, chamamos métodos neles. O `conversion.py` engata conversão markdown e NH3 sanitization.
- `src/pypub/ui/` - Visuais. Dependências de `PySide6`.

## Fluxo de Autenticação Segura
O Token de longa duração passa por `PKCE` com Local Callback Server. A aplicação Python abres um socket porta 8080 local via servidor cru e intercepta os Headers na Redireção. Zero "hardcoding". O Token morre lá e desce pro Wincred.

## Fluxo Híbrido do Editor
O PyQt RichText native Editor, quando convertido pra Markdown nativamente cria uma montanha inútil de spans errados. Nós isolamos a aba entre 4 vistas. Um motor de "Aviso de Destruição (is_dirty)" não permite que você perca a beleza de Rich Text virando um texto achatado Plain por erro de cliques.
