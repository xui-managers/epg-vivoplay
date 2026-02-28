#!/usr/bin/env python3
"""
Script para buscar EPG da API Vivo TV (Telefonica) e gerar epg.xml no formato XMLTV.
Chama todas as rotas de schedules e consolida canais e programação.
"""

import json
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
import requests

# Configuração
BASE_URL = "https://contentapi-br.cdn.telefonica.com/25/default/pt-BR/schedules"
FIELDS = "Pid,Title,Description,ChannelName,ChannelNumber,CallLetter,Start,End,EpgNetworkDvr,LiveChannelPid"
OUTPUT_FILE = "epg.xml"

# Cabeçalhos usados nas requisições
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Origin": "https://www.vivotv.com.br",
    "Pragma": "no-cache",
    "Referer": "https://www.vivotv.com.br/tv-guide/epg",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# Grupos de livechannelpids (uma requisição por grupo)
CHANNEL_GROUPS = [
    "lch5554,lch204,lch7184,lch7183,lch3649,lch3401,lch930,lch3131,lch4089,lch4071",
    "lch3087,lch7179,lch2889,lch4050,lch6520,lch891,lch3546,lch3648,lch3652,lch7185",
    "lch7182,lch81,lch151,lch1210,lch217,lch216,lch213,lch214,lch215,lch677",
    "lch56,lch3872,lch770,lch147,lch2443,lch5629,lch5630,lch2102,lch773,lch2794",
    "lch5631,lch6535,lch7195,lch2106,lch7120,lch6995,lch211,lch464,lch49,lch144",
    "lch855,lch3545,lch7180,lch7196,lch7181,lch7064,lch6485,lch5577,lch5573,lch5553",
    "lch2795,lch2067,lch2442,lch2091,lch4104,lch2066,lch6284,lch6285,lch7065,lch39",
    "lch769,lch2199,lch149,lch2449,lch1253,lch3286,lch3544,lch3651,lch7154,lch7155",
    "lch7190,lch6232,lch6540,lch7066,lch5552,lch3960,lch3874,lch1242,lch771,lch1252",
    "lch2055,lch2073,lch2792,lch128,lch2793,lch4103,lch2064,lch3379,lch5480,lch5581",
    "lch5580,lch157,lch152,lch158,lch150,lch2444,lch653,lch126,lch108,lch932",
    "lch2093,lch2080,lch936,lch79,lch929,lch7142,lch772,lch5578,lch6356,lch182",
    "lch459,lch462,lch460,lch461,lch76,lch933,lch7141,lch119,lch111,lch154",
    "lch155,lch112,lch218,lch3650,lch2090,lch2071,lch2172,lch2104,lch2105,lch123",
    "lch142,lch937,lch1995,lch1996,lch2440,lch2441,lch2439,lch5670,lch6936",
]


def get_time_range():
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=2)
    end = now + timedelta(days=2)
    return int(start.timestamp()), int(end.timestamp())


def fetch_schedules(starttime: int, endtime: int) -> list[dict]:
    params_base = {
        "ca_deviceTypes": "null|401",
        "ca_channelmaps": "185|null",
        "fields": FIELDS,
        "includeRelations": "Genre",
        "orderBy": "START_TIME:a",
        "filteravailability": "false",
        "includeAttributes": "ca_cpvrDisable,ca_descriptors,ca_blackout_target,ca_blackout_areas",
        "starttime": starttime,
        "endtime": endtime,
        "offset": 0,
        "limit": 1000,
    }
    all_programmes = []
    for i, livechannelpids in enumerate(CHANNEL_GROUPS):
        params = {**params_base, "livechannelpids": livechannelpids}
        url = f"{BASE_URL}?{urlencode(params)}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            data = r.json()
            content = data.get("Content") or []
            all_programmes.extend(content)
            print(f"  Rotas {i + 1}/{len(CHANNEL_GROUPS)}: {len(content)} programas")
        except requests.RequestException as e:
            print(f"  Erro na rota {i + 1}: {e}")
        except json.JSONDecodeError as e:
            print(f"  Erro ao decodificar JSON na rota {i + 1}: {e}")
        time.sleep(0.2)  # evita sobrecarga
    return all_programmes


def timestamp_to_xmltv(ts: int) -> str:
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.strftime("%Y%m%d%H%M%S +0000")


def escape_xml(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_epg_xml(programmes: list[dict], output_path: str) -> None:
    channels = {}  # LiveChannelPid -> { display_name, channel_number }
    for p in programmes:
        pid = p.get("LiveChannelPid")
        if not pid:
            continue
        if pid not in channels:
            name = p.get("ChannelName") or p.get("CallLetter") or pid
            num = p.get("ChannelNumber") or ""
            channels[pid] = {"display_name": name, "channel_number": num}

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<tv generator-info-name="epg-vivoplay" source-info-url="https://www.vivotv.com.br">',
    ]

    for ch_id, info in sorted(channels.items()):
        num = escape_xml(info["channel_number"])
        name = escape_xml(info["display_name"])
        lines.append(f'  <channel id="{escape_xml(ch_id)}">')
        if num:
            lines.append(f'    <display-name>{num}</display-name>')
        lines.append(f'    <display-name>{name}</display-name>')
        lines.append("  </channel>")

    for p in programmes:
        ch_id = p.get("LiveChannelPid")
        if not ch_id:
            continue
        start_ts = p.get("Start")
        end_ts = p.get("End")
        if start_ts is None or end_ts is None:
            continue
        start_str = timestamp_to_xmltv(start_ts)
        stop_str = timestamp_to_xmltv(end_ts)
        title = escape_xml((p.get("Title") or "").strip() or "Sem título")
        desc = escape_xml((p.get("Description") or "").strip())
        lines.append(f'  <programme start="{start_str}" stop="{stop_str}" channel="{escape_xml(ch_id)}">')
        lines.append(f"    <title>{title}</title>")
        if desc:
            lines.append(f"    <desc>{desc}</desc>")
        lines.append("  </programme>")

    lines.append("</tv>")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Arquivo gerado: {output_path} ({len(channels)} canais, {len(programmes)} programas)")


def main():
    print("EPG Vivo TV - Buscando programação...")
    starttime, endtime = get_time_range()
    print(f"Período: {datetime.fromtimestamp(starttime, tz=timezone.utc)} até {datetime.fromtimestamp(endtime, tz=timezone.utc)} (UTC)")
    programmes = fetch_schedules(starttime, endtime)
    if not programmes:
        print("Nenhum programa retornado. Verifique as URLs ou a rede.")
        return
    build_epg_xml(programmes, OUTPUT_FILE)


if __name__ == "__main__":
    main()
