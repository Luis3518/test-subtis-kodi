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


def make_request_with_status(url):
    """
    Make an HTTP GET request to the specified URL and return data with status code
    
    Args:
        url: The URL to request
    
    Returns:
        Tuple (response_data, status_code) where response_data is dictionary or None
    """
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', f'Kodi Subtis Addon/{__version__}')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            status_code = response.getcode()
            return json.loads(data.decode('utf-8')), status_code
    except urllib.error.HTTPError as e:
        return None, e.code
    except:
        return None, 0


def search_subtitles(item):
    """
    Search for subtitles based on file size and file name
    
    Args:
        item: Dictionary containing video information (file_size, file_name, etc.)
    
    Returns:
        List of subtitle results
    """
    subtitles_list = []
    
    # Log datos relevantes
    log("=" * 60)

    title = item.get('title', '')
    log(f"Title: '{title}'")
    
    file_name = item.get('file_name', '')
    log(f"File name: '{file_name}'")
    
    imdb_id = item.get('imdb', '')
    log(f"IMDb ID: '{imdb_id}'")
    
    file_size = item.get('file_size', 0)
    log(f"File size (bytes): {file_size}")

    
    if not file_name or not file_size:
        log("ERROR: File name or file size missing")
        return subtitles_list
    
    # Codificar el nombre del archivo para la URL
    encoded_filename = urllib.parse.quote(file_name)
    
    # Construir la URL de búsqueda por file_size y file_name
    search_url = f"{SUBTIS_API_BASE}/subtitle/file/name/{file_size}/{encoded_filename}"
    log(f"Search URL: {search_url}")
    
    # Hacer la petición a la API
    response_data, status_code = make_request_with_status(search_url)
    log(f"Response status code: {status_code}")
    
    if response_data:
        log(f"Response data: {response_data}")
    
    if not response_data or status_code != 200:
        log(f"No subtitles found or error occurred (status: {status_code})")
        return subtitles_list
    
    # Extraer información del subtítulo de la respuesta
    # La respuesta tiene estructura: { 'title': {...}, 'subtitle': {...}, ... }
    subtitle_data = response_data.get('subtitle', {})
    title_data = response_data.get('title', {})
    
    if not subtitle_data:
        log("No subtitle data found in response")
        return subtitles_list
    
    # Extraer el ID del subtítulo (para descarga)
    subtitle_id = subtitle_data.get('id')
    if not subtitle_id:
        log("No subtitle ID found")
        return subtitles_list
    
    # Información adicional
    subtitle_file_name = subtitle_data.get('subtitle_file_name', file_name)
    queried_times = subtitle_data.get('queried_times', 0)
    title_name = title_data.get('title_name', 'Unknown')
    year = title_data.get('year', '')
    rating = title_data.get('rating', 0)
    
    # Crear el ListItem para Kodi
    display_label = f"{title_name} ({year})" if year else title_name
    
    listitem = xbmcgui.ListItem(
        label="Spanish",
        label2=display_label
    )
    
    # Establecer rating (0-5 basado en rating de la película/show)
    rating_5 = str(int(min(5, rating / 2)))
    listitem.setArt({'icon': rating_5})
    
    # Propiedades del subtítulo
    listitem.setProperty("sync", "true")
    listitem.setProperty("hearing_imp", "false")
    
    # URL para descargar este subtítulo
    url = f"plugin://{__scriptid__}/?action=download&id={subtitle_id}"
    
    subtitles_list.append((url, listitem, False))
    
    log(f"Found {len(subtitles_list)} subtitle(s)")
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
    log("=" * 60)
    log(f"DOWNLOADING SUBTITLE ID: {subtitle_id}")
    
    # Crear el directorio temporal si no existe
    if not xbmcvfs.exists(__temp__):
        xbmcvfs.mkdirs(__temp__)
    
    # Construir la URL de descarga
    download_url = f"{SUBTIS_API_BASE}/subtitle/link/{subtitle_id}"
    log(f"Download URL: {download_url}")
    
    try:
        req = urllib.request.Request(download_url)
        req.add_header('User-Agent', f'Kodi Subtis Addon/{__version__}')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = response.getcode()
            log(f"Download response status code: {status_code}")
            
            subtitle_content = response.read().decode('utf-8')
            content_length = len(subtitle_content)
            log(f"Downloaded content length: {content_length} characters")
            
            # Log primeras líneas del subtítulo para debug
            first_lines = '\n'.join(subtitle_content.split('\n')[:5])
            log(f"First lines of subtitle:\n{first_lines}")
        
        # Guardar el subtítulo en el directorio temporal
        subtitle_path = os.path.join(__temp__, f"subtis_{subtitle_id}.srt")
        
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            f.write(subtitle_content)
        
        log(f"Subtitle saved to: {subtitle_path}")
        log("=" * 60)
        return [subtitle_path]
        
    except Exception as e:
        log(f"ERROR downloading subtitle: {str(e)}")
        log("=" * 60)
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
        
        # Extraer el nombre del archivo desde la ruta completa
        playing_file = xbmc.Player().getPlayingFile()
        item['file_name'] = os.path.basename(playing_file)
        
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
