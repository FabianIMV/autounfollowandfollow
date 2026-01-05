#!/usr/bin/env python3
"""
Script para descubrir y seguir perfiles interesantes en GitHub.
Estrategias:
- Búsqueda por lenguaje y ubicación.
- Seguidores de un usuario específico.
- Usuarios que han dado estrella a un repositorio.
"""

import os
import time
import requests
import logging
from typing import List, Set, Dict, Optional, Any
from follower_automation import GitHubFollowerManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubDiscovery(GitHubFollowerManager):
    def __init__(self):
        super().__init__()
        self.max_discovery_follows = int(os.getenv('MAX_DISCOVERY_FOLLOWS', '10'))
        # Ratio mínimo de siguiendo/seguidores para considerar que hace follow-back
        # Por ejemplo, 0.7 significa que sigue a al menos el 70% de las personas que le siguen
        self.min_follow_ratio = float(os.getenv('MIN_FOLLOW_RATIO', '0.5'))
        
    def discover_by_search(self, query: str) -> List[str]:
        """Buscar usuarios usando la API de búsqueda de GitHub"""
        logger.info(f"🔍 Buscando usuarios con query: '{query}'")
        url = f"{self.base_url}/search/users"
        params = {'q': query, 'per_page': 50}
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            items = response.json().get('items', [])
            return [user['login'] for user in items]
        else:
            logger.error(f"❌ Error en búsqueda: {response.status_code}")
            return []

    def discover_by_repo_stargazers(self, repo: str) -> List[str]:
        """Obtener usuarios que dieron estrella a un repo"""
        logger.info(f"⭐ Descubriendo desde stargazers de: {repo}")
        url = f"{self.base_url}/repos/{repo}/stargazers"
        params = {'per_page': 100}
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return [user['login'] for user in response.json()]
        return []

    def is_likely_to_follow_back(self, user_info: Dict[str, Any]) -> bool:
        """Determinar si un usuario es propenso a hacer follow-back basándose en su ratio"""
        followers = user_info.get('followers', 0)
        following = user_info.get('following', 0)
        
        if followers == 0:
            return True # Usuarios nuevos suelen ser buena opción
            
        ratio = following / followers
        if ratio >= self.min_follow_ratio:
            logger.info(f"✅ @{user_info['login']} tiene un buen ratio ({ratio:.2f}).")
            return True
        else:
            logger.info(f"⏭️  Saltando @{user_info['login']} (ratio bajo: {ratio:.2f})")
            return False

    def run_discovery(self, strategy: str, target: str):
        """Ejecutar la estrategia de descubrimiento"""
        logger.info(f"🚀 Iniciando descubrimiento | Estrategia: {strategy} | Target: {target}")
        
        usernames = []
        if strategy == 'search':
            usernames = self.discover_by_search(target)
        elif strategy == 'stargazers':
            usernames = self.discover_by_repo_stargazers(target)
        elif strategy == 'followers':
            followers = self.get_followers(target)
            usernames = [u['login'] for u in followers]
        
        if not usernames:
            logger.warning("⚠️ No se encontraron usuarios con esta estrategia.")
            return

        # Filtrar yo mismo y gente que ya sigo
        me = self.username.lower()
        following = {u['login'].lower() for u in self.get_following()}
        
        candidates = [u for u in usernames if u.lower() != me and u.lower() not in following]
        logger.info(f"📊 Encontrados {len(candidates)} candidatos potenciales.")

        followed_count = 0
        for username in candidates:
            if followed_count >= self.max_discovery_follows:
                break

            user_info = self.get_user_info(username)
            if not user_info:
                continue

            # Filtros de seguridad heredados
            if self.should_skip_user(user_info):
                continue
            
            # Nuevo filtro de probabilidad de follow-back
            if not self.is_likely_to_follow_back(user_info):
                continue
                
            if self.follow_user(username):
                followed_count += 1
                time.sleep(self.delay_between_actions)
        
        logger.info(f"✨ Descubrimiento completado. Seguiste a {followed_count} perfiles nuevos.")

def main():
    # Parámetros desde variables de entorno
    strategy = os.getenv('DISCOVERY_STRATEGY', 'search')
    target = os.getenv('DISCOVERY_TARGET', 'follow back')
    
    discovery = GitHubDiscovery()
    discovery.run_discovery(strategy, target)

if __name__ == "__main__":
    main()
