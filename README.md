# Test Subtitles Kodi Addon

Addon de servicio de subtítulos para Kodi.

## Características

- Compatible con Python 3.0.0 para Kodi
- Búsqueda automática de subtítulos
- Búsqueda manual
- Configuración de cuenta de usuario
- Soporte multiidioma (inglés y español)

## Estructura del Proyecto

```
.
├── addon.xml                   # Archivo de configuración del addon
├── service.py                  # Archivo principal del servicio
├── resources/
│   ├── settings.xml           # Configuración del addon
│   └── language/              # Traducciones
│       ├── resource.language.en_gb/
│       │   └── strings.po
│       └── resource.language.es_es/
│           └── strings.po
└── README.md
```

## Instalación

1. Empaqueta el addon en un archivo ZIP
2. En Kodi, ve a Addons > Instalar desde archivo ZIP
3. Selecciona el archivo ZIP del addon

## Desarrollo

Para adaptar este addon a tu servicio de subtítulos específico:

1. Modifica `addon.xml` con la información de tu addon (ID, nombre, autor)
2. Implementa la lógica de búsqueda en la función `search_subtitles()` en `service.py`
3. Implementa la lógica de descarga en la función `download_subtitle()` en `service.py`
4. Añade un icono del addon en `resources/icon.png` (256x256 px)

## API de Kodi para Subtítulos

El addon utiliza las siguientes acciones:

- `search`: Busca subtítulos automáticamente basándose en el video que se está reproduciendo
- `download`: Descarga un subtítulo específico
- `manualsearch`: Permite al usuario buscar subtítulos manualmente

## Propiedades de los ListItems

- `sync`: Indica si el subtítulo está sincronizado con el video
- `hearing_imp`: Indica si el subtítulo incluye ayudas auditivas
- `icon`: Calificación del subtítulo (0-5)

## Licencia

GPL-2.0-or-later
