# Release Guidelines

Este documento demarca os ritmos estritos da cadência de lançamento para o PyPub.

## Controle de Versão
Utilizamos Versionamento Semântico (`MAJOR.MINOR.PATCH`).
- **Major:** Mudanças na arquitetura de dependência pesadas (Mudança de ORM ou framework visual).
- **Minor:** Novas features completas para o usuário final (Ex.: Inserção de uma Side-to-Side Preview Pane).
- **Patch:** Hotfixes contidos.

## Processo de Release via GitHub
O PyPub possui Actions atreladas. Não crie Zips localmente, deixe a nuvem chancelar.

### Criando a Release:
1. No seu branch main localmente garanta estar num estado limpo:
   ```bash
   git switch main
   git pull
   ```
2. Adicione uma tag atrelada ao nome formatado em "vX.X.X":
   ```bash
   git tag v0.0.1
   git push origin v0.0.1
   ```
3. A pipeline do GitHub Actions (.github/workflows/build-windows.yml) acordará detectando a tag. Ela provisionará uma máquina virtual Windows, rodará `build.ps1` e fará zip da pasta construída e atachará na janela de release.

## Política Pós-Release (Updates)
Versões compiladas não carregam updaters silenciosos invisíveis para respeito ao usuário. Anúncios de Release e Links são delegados para o próprio repo em si.
