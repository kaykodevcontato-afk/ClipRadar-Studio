# ClipRadar Studio AI — Dev Kayko

Site para pesquisar referências de gameplay e **gerar Shorts com arquivos próprios ou autorizados**. A interface é compatível com GitHub Pages, mas a geração de vídeos requer iniciar o processador local.

## O que está pronto
- Busca YouTube Data API v3, com a chave informada na interface **sem ser gravada no repositório**.
- Vídeos do YouTube incorporados para referência (sem download de material do YouTube).
- Importação de arquivos MP4, MOV, MKV, AVI e WEBM de até 2 GB.
- Análise local de movimento e intensidade do áudio via OpenCV/FFmpeg.
- Criação de 1, 3 ou 5 montagens verticais com trechos escolhidos automaticamente, em MP4 H.264, 720×1280 ou 1080×1920.
- Configuração padrão: **GTA VI, 3 Shorts, 60 s, estilo viral**.
- Áudio do jogo preservado nos cortes quando presente.
- Títulos curtos + hashtags para copiar e uso opcional de legendas por voz (SRT e tentativa de legenda embutida no vídeo).
- Prévia e download dos resultados.

## Execução no Windows
1. Instale **Python 3.10+** (ative “Add Python to PATH” no instalador).
2. Instale **FFmpeg**, com os programas `ffmpeg` e `ffprobe` disponíveis no `PATH`. Com `winget`: `winget install Gyan.FFmpeg` e abra novo terminal após a instalação.
3. Extraia o ZIP inteiro. Clique duas vezes em `iniciar_windows.bat`.
4. Abra **http://127.0.0.1:8765** no mesmo computador. NÃO use o endereço do GitHub para gerar os MP4, pois o site estático não acessa o servidor local nesta configuração.
5. Envie uma gravação **de pelo menos 60 segundos** para criar Shorts de 60 segundos. Clique em **Gerar 3 Shorts verticais**.
6. Baixe os 3 arquivos MP4. Os resultados também são gravados em `workspace/<id do processamento>/`.

**Legendas por fala, opcionais:** com o ambiente virtual ativado, instale `pip install faster-whisper`. O primeiro uso baixa um modelo de reconhecimento de voz; é preciso internet nessa primeira instalação. O modelo configura português brasileiro, mas reconhecimento de outras línguas pode falhar. As legendas só aparecem se houver fala reconhecível. Se a biblioteca não estiver disponível, os MP4 ainda são produzidos sem legendas e o site mostrará um aviso. Para obter legendas embutidas, seu FFmpeg precisa ter o filtro `subtitles` (libass). Arquivos SRT são salvos separadamente.

## Execução Linux/macOS
Instale Python 3.10+, FFmpeg e dependências de vídeo; execute `bash iniciar_linux_mac.sh` e abra http://127.0.0.1:8765.

## Publicação no GitHub Pages
1. Crie um repositório, como `clipradar-studio`.
2. Copie o conteúdo da pasta `site/` para a raiz do repositório (pelo menos `index.html`).
3. Em **Settings > Pages**, selecione **Deploy from a branch**, `main`, pasta `/(root)` e salve.
4. O GitHub Pages mostrará a pesquisa do YouTube e a apresentação do produto; a geração local estará desativada no domínio publicado.
5. Se optar pela pesquisa incorporada, crie uma chave YouTube Data API v3 no Google Cloud, ative a API e restrinja a chave aos referers do seu domínio GitHub Pages e somente àquela API. A chave é informada na interface; **nunca a comite no repositório**. Considere que chaves fornecidas ao navegador são visíveis para quem as usa, por isso restrições e cotas são essenciais.

## Limitações importantes
- **GitHub Pages é hospedagem estática**: não executa Python, FFmpeg, análise de vídeo ou tarefas de longa duração. Para gerar MP4, use o processador no PC local. Para geração pela internet, será necessário implantar um backend e definir proteção, armazenamento e controle de custos.
- **Não baixa vídeos do YouTube:** a API de pesquisa não dá acesso a bytes de vídeo nem autoriza baixar ou reutilizar vídeos de terceiros. Use vídeos seus ou para os quais você tenha autorização.
- A “IA de cortes” desta versão é um **ranking automático baseado em movimento e volume de som**, não análise semântica avançada. Não detecta com confiabilidade vitórias, piadas, sustos ou cenas realmente virais.
- Se a gravação tem exatamente 60 segundos, gerar 3 vídeos de 60 segundos exige reutilizar material, portanto eles podem ficar muito parecidos. Para mais variedade, grave vários minutos.
- Não há renderização de efeitos de transição elaborados, narração gerada ou publicação automática no YouTube.
- A versão atual usa **recorte central 9:16**. Elementos nas bordas de vídeos horizontais podem ficar fora da imagem.
- Vídeos longos e exportação Full HD podem consumir muitos recursos. Use 720p primeiro.
- Arquivos permanecem no computador local e **não** são enviados para a nuvem pelo processador local.

## Estrutura
```text
site/index.html             interface GitHub Pages + modo local
backend/app.py              API HTTP local com upload, trabalho e downloads
backend/engine.py           análise, seleção, renderização, legendas opcionais
backend/requirements.txt    dependências mínimas
iniciar_windows.bat         inicialização no Windows
iniciar_linux_mac.sh        inicialização Linux/macOS
workspace/                  saída local, criada pelo programa
```

## Sobre YouTube e direitos
Use vídeos próprios ou que você tenha licença para editar e publicar. A pesquisa e o player são apenas para visualizar referências. O editor não extrai conteúdos do YouTube. Não use títulos que apresentem montagens fictícias como gameplay oficial de GTA VI.
