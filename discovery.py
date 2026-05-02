#!/usr/bin/env python3
"""
Script para descubrir y seguir perfiles interesantes en GitHub.
Estrategias:
- Búsqueda por lenguaje y ubicación.
- Seguidores de un usuario específico.
- Usuarios que han dado estrella a un repositorio.
- Búsqueda global de usuarios activos.
"""

import os
import time
import requests
import logging
from typing import List, Set, Dict, Optional, Any
from follower_automation import GitHubFollowerManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubDiscovery(GitHubFollowerManager):
    def __init__(self):
        super().__init__()
        self.max_discovery_follows = int(os.getenv('MAX_DISCOVERY_FOLLOWS', '10'))
        # Ratio mínimo: bajado de 0.5 a 0.3 para encontrar más candidatos
        self.min_follow_ratio = float(os.getenv('MIN_FOLLOW_RATIO', '0.3'))

    def discover_by_search(self, query: str) -> List[str]:
        """Buscar usuarios usando la API de búsqueda de GitHub"""
        logger.info(f"🔍 Buscando usuarios con query: '{query}'")
        url = f"{self.base_url}/search/users"
        # Aumentado a 100 resultados para tener más candidatos
        params = {'q': query, 'per_page': 100, 'sort': 'joined', 'order': 'desc'}

        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            items = response.json().get('items', [])
            logger.info(f"📊 Encontrados {len(items)} usuarios en la búsqueda.")
            return [user['login'] for user in items]
        else:
            logger.error(f"❌ Error en búsqueda: {response.status_code} - {response.text}")
            return []

    def discover_by_repo_stargazers(self, repo: str) -> List[str]:
        """Obtener usuarios que dieron estrella a un repo"""
        logger.info(f"⭐ Descubriendo desde stargazers de: {repo}")
        url = f"{self.base_url}/repos/{repo}/stargazers"
        params = {'per_page': 100}

        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            users = [user['login'] for user in response.json()]
            logger.info(f"📊 Encontrados {len(users)} stargazers.")
            return users
        logger.error(f"❌ Error obteniendo stargazers: {response.status_code}")
        return []

    def discover_by_trending(self) -> List[str]:
        """Descubrir usuarios buscando repos con muchas estrellas recientes"""
        logger.info("🔥 Descubriendo usuarios desde repos trending...")
        url = f"{self.base_url}/search/repositories"
        params = {
            'q': 'stars:>10 pushed:>2024-01-01',
            'sort': 'stars',
            'order': 'desc',
            'per_page': 20
        }
        response = requests.get(url, headers=self.headers, params=params)
        usernames = []
        if response.status_code == 200:
            repos = response.json().get('items', [])
            for repo in repos:
                owner = repo.get('owner', {}).get('login')
                if owner:
                    usernames.append(owner)
        logger.info(f"📊 Encontrados {len(usernames)} owners de repos trending.")
        return usernames

    def is_likely_to_follow_back(self, user_info: Dict[str, Any]) -> bool:
        """Determinar si un usuario es propenso a hacer follow-back"""
        followers = user_info.get('followers', 0)
        following = user_info.get('following', 0)
        username = user_info.get('login', '')

        # Usuarios nuevos (pocos followers) suelen seguir de vuelta
        if followers < 10:
            logger.info(f"✅ @{username} es usuario nuevo, buena candidatura.")
            return True

        # Si no sigue a nadie, no tiene sentido
        if following == 0:
            logger.info(f"⏭️  Saltando @{username} (no sigue a nadie)")
            return False

        ratio = following / max(followers, 1)
        if ratio >= self.min_follow_ratio:
            logger.info(f"✅ @{username} tiene buen ratio ({ratio:.2f}).")
            return True
        else:
            logger.info(f"⏭️  Saltando @{username} (ratio bajo: {ratio:.2f})")
            return False

    def run_discovery(self, strategy: str, target: str):
        """Ejecutar la estrategia de descubrimiento"""
        logger.info(f"🚀 Iniciando descubrimiento | Estrategia: {strategy} | Target: '{target}'")

        usernames = []
        if strategy == 'search':
            usernames = self.discover_by_search(target)
        elif strategy == 'stargazers':
            usernames = self.discover_by_repo_stargazers(target)
        elif strategy == 'followers':
            followers = self.get_followers(target)
            usernames = [u['login'] for u in followers]
        elif strategy == 'trending':
            usernames = self.discover_by_trending()

        if not usernames:
            logger.warning("⚠️ No se encontraron usuarios con esta estrategia.")
            return

        # Filtrar yo mismo y gente que ya sigo
        me = self.username.lower()
        following = {u['login'].lower() for u in self.get_following()}

        candidates = [u for u in usernames if u.lower() != me and u.lower() not in following]
        logger.info(f"📊 {len(candidates)} candidatos nuevos (filtrando los que ya sigues).")

        if not candidates:
            logger.info("ℹ️  Ya sigues a todos los candidatos encontrados. Prueba cambiar el target.")
            return

        followed_count = 0
        for username in candidates:
            if followed_count >= self.max_discovery_follows:
                logger.info(f"🏁 Límite de {self.max_discovery_follows} follows de descubrimiento alcanzado.")
                break

            user_info = self.get_user_info(username)
            if not user_info:
                continue

            # Filtros de seguridad heredados
            if self.should_skip_user(user_info):
                continue

            # Filtro de probabilidad de follow-back
            if not self.is_likely_to_follow_back(user_info):
                continue

            if self.follow_user(username):
                followed_count += 1
                time.sleep(self.delay_between_actions)

        logger.info(f"✨ Descubrimiento completado. Seguiste a {followed_count} perfiles nuevos.")

def main():
    strategy = os.getenv('DISCOVERY_STRATEGY', 'search')
    # Target mejorado: busca developers activos en lugar de "follow back"
    target = os.getenv('DISCOVERY_TARGET', 'type:user followers:>5 repos:>3')

    discovery = GitHubDiscovery()
    discovery.run_discovery(strategy, target)

if __name__ == "__main__":
    main()
