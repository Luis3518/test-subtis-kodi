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

SUBTIS_API_BASE = "https://api.subt.is/v1"


def log(msg):
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
        req = urllib.request.Request(url)
        req.add_header('User-Agent', f'Kodi Subtis Addon/{__version__}')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            return json.loads(data.decode('utf-8'))
    except:
        return None


def search_subtitles(item):
    """
    Search for subtitles based on the video item information
    
    Args:
        item: Dictionary containing video information (title, year, season, episode, etc.)
    
    Returns:
        List of subtitle results
    """
    subtitles_list = []
    
    # Log datos relevantes
    log("=" * 60)

    title = item.get('title', '')
    log(f"Title: '{title}'")
    
    imdb_id = item.get('imdb', '')
    log(f"IMDb ID: '{imdb_id}'")
    
    file_size = item.get('file_size', 0)
    log(f"File size (bytes): {file_size}")

    
    if not title:
        return subtitles_list
    
    # Codificar el nombre para la URL
    encoded_title = urllib.parse.quote(title)
    
    # Construir la URL de búsqueda de títulos
    search_url = f"{SUBTIS_API_BASE}/titles/search/{encoded_title}"
    
    # Hacer la petición a la API
    response_data = make_request(search_url)
    
    if not response_data:
        return subtitles_list
    
    # Obtener los resultados del JSON
    results = response_data.get('results', [])
    
    if not results:
        return subtitles_list
    
    # Procesar cada resultado
    for idx, result in enumerate(results):
        subtitle_id = result.get('id')
        title_name = result.get('title_name', 'Unknown')
        title_name_spa = result.get('title_name_spa', title_name)
        year = result.get('year', '')
        rating = result.get('rating', 0)
        title_type = result.get('type', 'movie')
        
        # Usar el nombre en español si está disponible
        display_name = title_name_spa if title_name_spa else title_name
        filename = f"{display_name} ({year})"
        
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
    # Crear el directorio temporal si no existe
    if not xbmcvfs.exists(__temp__):
        xbmcvfs.mkdirs(__temp__)
    
    # Construir la URL de descarga
    download_url = f"{SUBTIS_API_BASE}/subtitle/link/{subtitle_id}"
    
    try:
        req = urllib.request.Request(download_url)
        req.add_header('User-Agent', f'Kodi Subtis Addon/{__version__}')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            subtitle_content = response.read().decode('utf-8')
        
        # Guardar el subtítulo en el directorio temporal
        subtitle_path = os.path.join(__temp__, f"subtis_{subtitle_id}.srt")
        
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            f.write(subtitle_content)
        
        return [subtitle_path]
        
    except Exception as e:
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
        item['imdb'] = xbmc.getInfoLabel("VideoPlayer.IMDBNumber")
        
        # Get file size in bytes
        try:
            playing_file = xbmc.Player().getPlayingFile()
            if xbmcvfs.exists(playing_file):
                stat = xbmcvfs.Stat(playing_file)
                item['file_size'] = stat.st_size()
            else:
                item['file_size'] = 0
        except Exception as e:
            log(f"Could not get file size: {str(e)}")
            item['file_size'] = 0
        
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
    
    elif action == 'manualsearch':
        # Búsqueda manual (el usuario introduce el texto)
        searchstring = params.get('searchstring')
        # Implementar búsqueda manual similar a search
    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


if __name__ == '__main__':
    main()
