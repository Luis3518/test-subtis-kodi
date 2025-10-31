# -*- coding: utf-8 -*-

import os
import sys
import json
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
import urllib.parse
import urllib.request
import urllib.error

__addon__ = xbmcaddon.Addon()
__author__ = __addon__.getAddonInfo('author')
__scriptid__ = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__language__ = __addon__.getLocalizedString

__profile__ = xbmcvfs.translatePath(__addon__.getAddonInfo('profile'))
__temp__ = xbmcvfs.translatePath(os.path.join(__profile__, 'temp', ''))

# API Configuration
SUBTIS_API_BASE = "https://api.subt.is/v1"


def log(msg):
    """Log a message to the Kodi log file"""
    xbmc.log(f"### SUBTIS ### {msg}", level=xbmc.LOGINFO)


def make_request(url):
    """
    Make an HTTP GET request to the specified URL
    
    Args:
        url: The URL to request
    
    Returns:
        Dictionary with the JSON response or None if error
    """
    try:
        log(f"Making request to: {url}")
        req = urllib.request.Request(url)
        req.add_header('User-Agent', f'Kodi Subtis Addon/{__version__}')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            return json.loads(data.decode('utf-8'))
    except urllib.error.HTTPError as e:
        log(f"HTTP Error: {e.code} - {e.reason}")
        return None
    except urllib.error.URLError as e:
        log(f"URL Error: {e.reason}")
        return None
    except Exception as e:
        log(f"Error making request: {str(e)}")
        return None


def search_subtitles(item):
    """
    Search for subtitles based on the video item information
    
    Args:
        item: Dictionary containing video information (title, year, season, episode, etc.)
    
    Returns:
        List of subtitle results
    """
    log("=" * 60)
    log("STARTING SUBTITLE SEARCH")
    log(f"Item data: {item}")
    
    subtitles_list = []
    
    # Obtener el nombre de la película/serie
    title = item.get('title', '')
    log(f"Extracted title: '{title}'")
    
    if not title:
        log("ERROR: No title found, cannot search")
        return subtitles_list
    
    # Codificar el nombre para la URL
    encoded_title = urllib.parse.quote(title)
    log(f"Encoded title: '{encoded_title}'")
    
    # Construir la URL de búsqueda de títulos
    search_url = f"{SUBTIS_API_BASE}/titles/search/{encoded_title}"
    log(f"Search URL: {search_url}")
    
    # Hacer la petición a la API
    log("Making API request...")
    response_data = make_request(search_url)
    log(f"API response received: {response_data is not None}")
    
    if not response_data:
        log("ERROR: No response from API")
        return subtitles_list
    
    total_results = response_data.get('total', 0)
    log(f"API returned {total_results} total results")
    
    # Obtener los resultados del JSON
    results = response_data.get('results', [])
    log(f"Results array length: {len(results)}")
    
    if not results:
        log("WARNING: No results in response array")
        return subtitles_list
    
    # Procesar cada resultado
    for idx, result in enumerate(results):
        log(f"Processing result {idx + 1}/{len(results)}")
        
        subtitle_id = result.get('id')
        title_name = result.get('title_name', 'Unknown')
        title_name_spa = result.get('title_name_spa', title_name)
        year = result.get('year', '')
        rating = result.get('rating', 0)
        title_type = result.get('type', 'movie')
        
        log(f"  - ID: {subtitle_id}")
        log(f"  - Title: {title_name}")
        log(f"  - Title (Spanish): {title_name_spa}")
        log(f"  - Year: {year}")
        log(f"  - Rating: {rating}")
        log(f"  - Type: {title_type}")
        
        # Usar el nombre en español si está disponible
        display_name = title_name_spa if title_name_spa else title_name
        filename = f"{display_name} ({year})"
        
        log(f"Creating ListItem with filename: {filename}")
        
        # Crear el ListItem para Kodi
        listitem = xbmcgui.ListItem(
            label="Spanish",  # Idioma (subt.is parece ser principalmente español)
            label2=filename
        )
        
        # Establecer la calificación (0-5)
        # Convertir rating de 0-10 a 0-5
        rating_5 = str(int(min(5, rating / 2)))
        listitem.setArt({'icon': rating_5})
        
        # Propiedades del subtítulo
        listitem.setProperty("sync", "false")
        listitem.setProperty("hearing_imp", "false")
        
        # URL para descargar este subtítulo
        url = f"plugin://{__scriptid__}/?action=download&id={subtitle_id}"
        
        subtitles_list.append((url, listitem, False))
        log(f"Subtitle {idx + 1} added to list successfully")
    
    log(f"SEARCH COMPLETE: Returning {len(subtitles_list)} subtitles")
    log("=" * 60)
    return subtitles_list


def get_language_name(language_code):
    """
    Convert language code to full language name
    
    Args:
        language_code: ISO language code (e.g., 'es', 'en')
    
    Returns:
        Full language name
    """
    languages = {
        'es': 'Spanish',
        'en': 'English',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
    }
    return languages.get(language_code.lower(), language_code.upper())


def download_subtitle(subtitle_id):
    """
    Download a specific subtitle from subt.is API
    
    Args:
        subtitle_id: The ID of the subtitle to download
    
    Returns:
        List with the path to the downloaded subtitle file
    """
    log(f"Downloading subtitle with ID: {subtitle_id}")
    
    # Crear el directorio temporal si no existe
    if not xbmcvfs.exists(__temp__):
        xbmcvfs.mkdirs(__temp__)
    
    # Construir la URL de descarga
    download_url = f"{SUBTIS_API_BASE}/subtitle/link/{subtitle_id}"
    
    try:
        log(f"Downloading from: {download_url}")
        req = urllib.request.Request(download_url)
        req.add_header('User-Agent', f'Kodi Subtis Addon/{__version__}')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            subtitle_content = response.read().decode('utf-8')
        
        # Guardar el subtítulo en el directorio temporal
        subtitle_path = os.path.join(__temp__, f"subtis_{subtitle_id}.srt")
        
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            f.write(subtitle_content)
        
        log(f"Subtitle saved to: {subtitle_path}")
        return [subtitle_path]
        
    except Exception as e:
        log(f"Error downloading subtitle: {str(e)}")
        return []


def get_params():
    """Parse the plugin parameters"""
    params = {}
    paramstring = sys.argv[2]
    
    if len(paramstring) >= 2:
        params = dict(urllib.parse.parse_qsl(paramstring[1:]))
        
    return params


def main():
    """Main entry point for the addon"""
    params = get_params()
    
    log("=" * 80)
    log(f"ADDON STARTED - Version: {__version__}")
    log(f"sys.argv: {sys.argv}")
    log(f"Parsed params: {params}")
    log("=" * 80)
    
    action = params.get('action')
    log(f"Action requested: {action}")
    
    if action == 'search':
        # Obtener información del video actual
        item = {}
        item['temp'] = False
        item['rar'] = False
        item['year'] = xbmc.getInfoLabel("VideoPlayer.Year")
        item['season'] = str(xbmc.getInfoLabel("VideoPlayer.Season"))
        item['episode'] = str(xbmc.getInfoLabel("VideoPlayer.Episode"))
        item['tvshow'] = xbmc.getInfoLabel("VideoPlayer.TVshowtitle")
        item['title'] = xbmc.getInfoLabel("VideoPlayer.OriginalTitle")
        item['file_original_path'] = urllib.parse.unquote(
            xbmc.Player().getPlayingFile()
        )
        
        if item['title'] == "":
            item['title'] = xbmc.getInfoLabel("VideoPlayer.Title")
        
        log("Video Information:")
        log(f"  - Title: {item['title']}")
        log(f"  - Year: {item['year']}")
        log(f"  - Season: {item['season']}")
        log(f"  - Episode: {item['episode']}")
        log(f"  - TV Show: {item['tvshow']}")
        log(f"  - File Path: {item['file_original_path']}")
        
        # Buscar subtítulos
        subtitles_list = search_subtitles(item)
        
        log(f"Total subtitles found to add: {len(subtitles_list)}")
        
        # Agregar los resultados a Kodi
        for idx, subtitle in enumerate(subtitles_list):
            log(f"Adding subtitle {idx + 1}: {subtitle[0]}")
            xbmcplugin.addDirectoryItem(
                handle=int(sys.argv[1]),
                url=subtitle[0],
                listitem=subtitle[1],
                isFolder=False
            )
    
    elif action == 'download':
        # Descargar el subtítulo específico
        subtitle_id = params.get('id')
        
        if subtitle_id:
            subtitle_list = download_subtitle(subtitle_id)
            
            # Informar a Kodi sobre el archivo descargado
            for subtitle in subtitle_list:
                listitem = xbmcgui.ListItem(label=subtitle)
                xbmcplugin.addDirectoryItem(
                    handle=int(sys.argv[1]),
                    url=subtitle,
                    listitem=listitem,
                    isFolder=False
                )
        else:
            log("No subtitle ID provided for download")
    
    elif action == 'manualsearch':
        # Búsqueda manual (el usuario introduce el texto)
        searchstring = params.get('searchstring')
        log(f"Manual search for: {searchstring}")
        # Implementar búsqueda manual similar a search
    
    else:
        log(f"WARNING: Unknown action '{action}'")
    
    log("Calling endOfDirectory")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    log("Addon execution complete")
    log("=" * 80)


if __name__ == '__main__':
    main()
