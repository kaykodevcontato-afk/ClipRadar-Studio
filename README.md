# ClipRadar Studio — Dev Kayko

Site estático para GitHub Pages: pesquisa de vídeos no YouTube (com chave opcional da YouTube Data API v3), referência para montagem de vídeos, importação local de gameplay, seleção/reordenação de trechos e exportação vertical 9:16 como WebM.

## Publicar
1. Crie um repositório público no GitHub.
2. Envie `index.html` para a raiz.
3. Abra Settings → Pages → Build and deployment → Deploy from a branch → main / (root) → Save.
4. Acesse a URL do GitHub Pages que aparecer.

## Busca integrada
Crie uma chave no Google Cloud Console, habilite **YouTube Data API v3**, restrinja a chave ao domínio do seu GitHub Pages usando *HTTP referrers* e cole no campo do site. A chave não é salva no navegador nem incluída no código. Sem chave, o botão abre a pesquisa diretamente no YouTube.

## Edição
Importe apenas gameplay seu ou com autorização. A API do YouTube não permite que este site obtenha arquivos de vídeos arbitrários para recorte. A função "Sugerir cortes" distribui intervalos; **não** detecta momentos importantes com IA. A exportação grava a reprodução em tempo real no navegador, então pode demorar a duração completa do Short. Priorize Chrome/Edge e mantenha a aba aberta. Exportação WebM; use CapCut para converter a MP4, se necessário. A reprodução/áudio e codecs variam entre navegadores.

## Privacidade
O arquivo de vídeo é processado no navegador. O único envio para serviço externo é a busca de metadados à API do YouTube, se ativada. As configurações de texto podem ser salvas no armazenamento local.
