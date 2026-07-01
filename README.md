# GitHub Follower Automation 🤖

Script y flujo de trabajo de GitHub Actions para automatizar el manejo de seguidores en GitHub.

## ✨ Características

- 🧹 **Autounfollow**: Deja de seguir a quienes no te siguen de vuelta.
- 🤝 **Autofollow**: Sigue automáticamente a tus seguidores.
- 🛡️ **Whitelist**: Protege a usuarios específicos para que nunca sean eliminados (vía `whitelist.txt`).
- 🧪 **Dry Run**: Prueba los cambios sin ejecutarlos realmente.
- 📊 **Estadísticas**: Resumen detallado de seguidores, seguidos y ratio.
- 🚀 **GitHub Actions**: Automatización diaria totalmente configurable.

## 🛠️ Instalación Local 

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export GITHUB_TOKEN="tu_token_aqui"
export GITHUB_USERNAME="tu_usuario"

# Ejecutar (modo prueba por defecto si configuras DRY_RUN=true)
export DRY_RUN=true
python follower_automation.py
```

## ⚙️ Configuración (GitHub Actions)

1. Ve a **Settings > Secrets and variables > Actions**.
2. Añade un **Repository secret** llamado `PERSONAL_GITHUB_TOKEN` con permisos de `user:follow`.
3. (Opcional) Configura variables como `MAX_UNFOLLOWS_PER_RUN` o `DELAY_SECONDS`.

### 🛡️ Uso de Whitelist

Crea o edita el archivo `whitelist.txt` y añade un nombre de usuario por línea. El script ignorará a estos usuarios durante el proceso de limpieza.

## 🔎 Descubrimiento de Perfiles

El nuevo script `discovery.py` te permite encontrar gente interesante para seguir.

### Uso Local

```bash
# Buscar gente que hace "follow back" globalmente
export DISCOVERY_STRATEGY="search"
export DISCOVERY_TARGET="follow back"
python discovery.py

# Buscar gente usando el hashtag "f4f" (follow for follow)
export DISCOVERY_STRATEGY="search"
export DISCOVERY_TARGET="f4f"
python discovery.py
```

## 📄 Licencia
- Choose: `both`, `follow_back`, `cleanup`, or `stats_only`

## Configuration:
Set variables in repository settings:
- `MAX_UNFOLLOWS_PER_RUN`: Max unfollows per day (default: 20)
- `MAX_FOLLOWS_PER_RUN`: Max follows per day (default: 15)
- `DELAY_SECONDS`: Seconds between actions (default: 5)

## Safety Features:
- 🛡️ Skips users with 10,000+ followers
- 🛡️ Skips GitHub organizations  
- ⏱️ Respects API rate limits
- 📊 Full transparency in logs

**Result**: Clean follower ratio where you only follow people who follow you back.

---

*Created with ❤️ by Claude and [@FabianIMV](https://github.com/FabianIMV)*
