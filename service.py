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
    xbmc.log(f"{__scriptname__} v{__version__}: {msg}", level=xbmc.LOGDEBUG)


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
    log(f"Searching subtitles for: {item}")
    
    subtitles_list = []
    
    # Obtener el nombre de la película/serie
    title = item.get('title', '')
    if not title:
        log("No title found, cannot search")
        return subtitles_list
    
    # Codificar el nombre para la URL
    encoded_title = urllib.parse.quote(title)
    
    # Construir la URL de búsqueda
    search_url = f"{SUBTIS_API_BASE}/titles/search/{encoded_title}"
    
    # Hacer la petición a la API
    response_data = make_request(search_url)
    
    if not response_data:
        log("No response from API")
        return subtitles_list
    
    log(f"API Response: {response_data}")
    
    # Procesar los resultados
    # La estructura exacta depende de la respuesta de la API
    # Ajusta según la respuesta real de subt.is
    results = response_data if isinstance(response_data, list) else [response_data]
    
    for result in results:
        # Adaptar según la estructura real de la respuesta
        subtitle_id = result.get('id', '')
        filename = result.get('filename', result.get('name', 'Unknown'))
        language = result.get('language', 'es')
        language_name = get_language_name(language)
        rating = result.get('rating', 0)
        
        # Crear el ListItem para Kodi
        listitem = xbmcgui.ListItem(
            label=language_name,
            label2=filename
        )
        
        # Establecer la calificación (0-5)
        listitem.setArt({'icon': str(min(5, int(rating)))})
        
        # Propiedades del subtítulo
        listitem.setProperty("sync", "false")
        listitem.setProperty("hearing_imp", "false")
        
        # URL para descargar este subtítulo
        url = f"plugin://{__scriptid__}/?action=download&id={subtitle_id}"
        
        subtitles_list.append((url, listitem, False))
    
    log(f"Found {len(subtitles_list)} subtitles")
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
    Download a specific subtitle
    
    Args:
        subtitle_id: The ID of the subtitle to download
    
    Returns:
        List with the path to the downloaded subtitle file
    """
    log(f"Downloading subtitle: {subtitle_id}")
    
    # Crear el directorio temporal si no existe
    if not xbmcvfs.exists(__temp__):
        xbmcvfs.mkdirs(__temp__)
    
    # Aquí implementarías la lógica para descargar el subtítulo
    # Por ejemplo, hacer una petición HTTP para descargar el archivo
    
    # Ejemplo: guardar el subtítulo descargado
    subtitle_path = os.path.join(__temp__, f"{subtitle_id}.srt")
    
    # Simular descarga (reemplazar con tu lógica real)
    # with open(subtitle_path, 'w', encoding='utf-8') as f:
    #     f.write("1\n00:00:01,000 --> 00:00:04,000\nEjemplo de subtítulo\n\n")
    
    return [subtitle_path]


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
    
    action = params.get('action')
    
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
        
        # Buscar subtítulos
        subtitles_list = search_subtitles(item)
        
        # Agregar los resultados a Kodi
        for subtitle in subtitles_list:
            xbmcplugin.addDirectoryItem(
                handle=int(sys.argv[1]),
                url=subtitle[0],
                listitem=subtitle[1],
                isFolder=False
            )
    
    elif action == 'download':
        # Descargar el subtítulo específico
        subtitle_id = params.get('id')
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
    
    elif action == 'manualsearch':
        # Búsqueda manual (el usuario introduce el texto)
        searchstring = params.get('searchstring')
        log(f"Manual search for: {searchstring}")
        # Implementar búsqueda manual similar a search
    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


if __name__ == '__main__':
    main()
