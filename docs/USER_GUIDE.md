# PyPub User Guide

Bem-vindo ao PyPub, sua ferramenta desktop para mandar mensagens, anotações de micro-blog e long-form articles, independentemente da web sem fechar o navegador.

## Como Adicionar sua Conta
1. Ao iniciar o App na tela inicial, clique em **Add Account (IndieAuth)**.
2. Você precisará informar sua **URL Root**. (Ex.: `https://meublog.com/`).
3. O PyPub tentará ler cabeçalhos na página (Endpoints Micropub/Tokens/Auth).
4. Siga as janelas abertas em seu browser nativo para a tela de autenticação do seu servidor.
5. Permita os escopos (`create update delete media`).
6. Cuidado! O Token nunca expira pra você a não ser que revogado no provedor.

## O Workspace (Escrevendo e Publicando)
No painel lateral clique em **Compose**. É ali que a magia reside.
* **Presets:** Escolha "note" para microtextos, ou "article" para blogs. O PyPub manda tags padrão baseadas em sua escolha.
* **Modos de Editor:**
  - **Rich Text:** O que você vê é o que tem, cole imagens do Word ou arraste, use atalhos (Ctrl+B, Ctrl+I).
  - **Markdown:** Edição direta crua para puristas. O PyPub tentará converter sempre pra HTML via servidor, mantendo as raízes.
  - **HTML:** Escreva as tags na mão.
  - **Plain:** Texto cru, ideal para pequenas 'notes'.
* **Painel Mídia:** Anexe imagens. O painel cuidará de subir ao endpoint `/media` e reincorporar o URL ao corpo final do Post *automaticamente*.

## Recuperação e Abas
Notou a etiqueta "Unsaved Changes" (Mudanças não salvas)?
A cada vez que você pausa de digitar por mais de dois segundos, salvamos em segundo plano. Desligue sua máquina. No próximo boot, vá até a aba "Drafts" e retome seu trabalho, bit a bit intacto.
