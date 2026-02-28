# EPG Vivo Play

Projeto para obter a grade de programação (EPG) dos canais da **Vivo TV** e gerar um arquivo **XMLTV** (`epg.xml`) que pode ser usado em players de IPTV, aplicativos e set-top boxes.

## Ideia do projeto

A Vivo TV expõe a programação via API da Telefonica (Content API). Este repositório:

1. **Consolida a grade** — Chama todas as rotas de *schedules* da API (por grupos de canais) e junta tudo em um único arquivo.
2. **Gera XMLTV** — O formato [XMLTV](https://github.com/XMLTV/xmltv) é suportado pela maioria dos softwares de IPTV (VLC, Kodi, TiviMate, etc.).
3. **Atualiza automaticamente** — Um workflow do GitHub Actions roda todo dia às 02:00 UTC, gera o `epg.xml` e faz commit no repositório.

O período da grade gerada é **2 horas no passado** e **2 dias à frente**, para cobrir atrasos e uso em guias de programação.

## Requisitos

- Python 3.10+
- `requests` (ver `requirements.txt`)

## Uso local

```bash
# Clone o repositório (se ainda não tiver)
git clone https://github.com/SEU_USUARIO/epg-vivoplay.git
cd epg-vivoplay

# Instale as dependências
pip install -r requirements.txt

# Gere o epg.xml
python retrieve.py
```

O arquivo **`epg.xml`** será criado na raiz do projeto.

## Como usar o EPG

### 1. URL do EPG

Basta utilziar a raw do github que voce ja consegue usar completamente o EPG automatico

```
https://raw.githubusercontent.com/xui-managers/epg-vivoplay/main/epg.xml
```

### 2. Em players / apps de IPTV

- **TiviMate, IPTV Smarters, etc.** — Na configuração da playlist ou do EPG, informe a URL do `epg.xml` (a URL raw acima) ou faça upload do arquivo, conforme a opção do app.
- **VLC** — Abra a playlist M3U e, nas preferências de programação, aponte para o arquivo ou URL do EPG.
- **Kodi (IPTV Simple Client)** — No add-on, em “EPG”, use “URL” e cole a URL do `epg.xml`.

Em todos os casos, o **identificador do canal** no EPG é o `LiveChannelPid` (ex.: `LCH7182`). A playlist M3U precisa usar o mesmo valor no atributo `tvg-id` (ou equivalente) para o EPG ser vinculado corretamente ao canal, por exemplo:

```m3u
#EXTINF:-1 tvg-id="LCH7182" tvg-name="GE",GE
http://...
```

### 3. Servir o arquivo você mesmo

Se preferir hospedar o `epg.xml` no seu próprio servidor ou CDN:

1. Rode `python retrieve.py` no servidor (ou use um cron) ou baixe o arquivo do repositório.
2. Sirva o arquivo via HTTP/HTTPS.
3. Use essa URL nos players.

## Estrutura do repositório

| Arquivo / pasta        | Descrição |
|------------------------|-----------|
| `retrieve.py`          | Script que chama a API e gera o `epg.xml` |
| `epg.xml`              | Grade em formato XMLTV (gerado pelo script ou pelo Actions) |
| `requirements.txt`     | Dependência Python (`requests`) |
| `.github/workflows/`   | Workflow que executa o script diariamente e faz commit do `epg.xml` |

## Atualização automática 

Após rodar, se o `epg.xml` tiver mudanças, o Actions faz commit e push no repositório, mantendo a grade sempre atualizada.

## Aviso

Este projeto apenas consome a API pública de programação (como o site da Vivo TV faz). O uso do EPG deve respeitar os termos de uso da Vivo e da operadora. O repositório não inclui nem distribui links de streaming.
