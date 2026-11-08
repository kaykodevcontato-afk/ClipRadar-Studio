# ClipRadar Studio — GitHub Pages

Site estático para pesquisar vídeos do YouTube (YouTube Data API v3), assistir às prévias e criar Shorts verticais **a partir de um arquivo local que você tenha direito de editar**.

## Publicar

1. Crie um repositório no GitHub.
2. Envie `index.html` para a raiz.
3. Em Settings > Pages, escolha Deploy from a branch, main, / (root).
4. Abra o site publicado.

## Usar

1. Crie uma chave YouTube Data API v3 no Google Cloud; restrinja sua chave por HTTP referrer e por API. Não grave a chave no repositório.
2. No site, digite GTA VI e cole a chave na pesquisa para ver os vídeos dentro da página.
3. Selecione `Assistir aqui` para ver um vídeo de referência incorporado.
4. Para editar, carregue na etapa 2 um MP4/WebM próprio ou autorizado. A pesquisa e a prévia não fornecem o arquivo de vídeo.
5. Adicione os trechos, configure o corte vertical e clique em `Gerar Short vertical`.
6. Ao terminar, clique no botão de download para obter um arquivo WebM.

## Limitações

- A YouTube Data API v3 permite pesquisar e incorporar vídeos, mas **não** permite baixar vídeos diretamente. As políticas da API proíbem baixar conteúdo audiovisual sem aprovação prévia por escrito.
- O botão `Sugerir cortes` distribui trechos; não é análise inteligente por IA.
- A exportação usa MediaRecorder, funciona melhor em Chrome/Edge e leva tempo de reprodução real. O resultado é WebM; para MP4, use um conversor/editor.
- GitHub Pages é hospedagem estática: não roda processamento de vídeos no servidor.
