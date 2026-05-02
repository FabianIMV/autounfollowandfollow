#!/usr/bin/env python3
"""
Script para automatizar el manejo de seguidores en GitHub
Funcionalidades:
- Dejar de seguir a usuarios que no te siguen de vuelta
- Seguir a usuarios que te siguen pero tú no los sigues
- Lista blanca (whitelist) para proteger usuarios específicos
- Modo de prueba (dry-run) para verificar acciones sin ejecutarlas
"""

import os
import time
import requests
import logging
from datetime import datetime
from typing import List, Set, Dict, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubFollowerManager:
    def __init__(self):
        # Token de GitHub desde variables de entorno
        self.token = os.getenv('GITHUB_TOKEN')
        self.username = os.getenv('GITHUB_USERNAME')

        # Configuraciones de seguridad
        self.max_unfollows_per_run = int(os.getenv('MAX_UNFOLLOWS_PER_RUN', '20'))
        self.max_follows_per_run = int(os.getenv('MAX_FOLLOWS_PER_RUN', '15'))
        self.delay_between_actions = int(os.getenv('DELAY_SECONDS', '5'))
        self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'

        # Whitelist
        self.whitelist_file = os.getenv('WHITELIST_FILE', 'whitelist.txt')
        self.whitelist = self._load_whitelist()

        # Headers para la API de GitHub
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': f'{self.username}-follower-automation'
        }

        # Base URL de la API de GitHub
        self.base_url = 'https://api.github.com'

    def _load_whitelist(self) -> Set[str]:
        """Cargar lista blanca de usuarios desde un archivo"""
        whitelist = set()
        if os.path.exists(self.whitelist_file):
            try:
                with open(self.whitelist_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            whitelist.add(line.lower())
                logger.info(f"📋 Whitelist cargada: {len(whitelist)} usuarios")
            except Exception as e:
                logger.error(f"❌ Error cargando whitelist: {e}")
        return whitelist

    def get_followers(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener lista de seguidores"""
        if not username:
            username = self.username

        followers = []
        page = 1
        per_page = 100

        logger.info(f"🔍 Obteniendo seguidores de {username}...")

        while True:
            url = f"{self.base_url}/users/{username}/followers"
            params = {'page': page, 'per_page': per_page}

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                page_followers = response.json()
                if not page_followers:
                    break

                followers.extend(page_followers)
                logger.info(f"   📄 Página {page}: {len(page_followers)} seguidores")
                page += 1
                time.sleep(0.5)
            else:
                logger.error(f"❌ Error obteniendo seguidores: {response.status_code}")
                break

        return followers

    def get_following(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtener lista de usuarios que sigo"""
        if not username:
            username = self.username

        following = []
        page = 1
        per_page = 100

        logger.info(f"🔍 Obteniendo usuarios que sigue {username}...")

        while True:
            url = f"{self.base_url}/users/{username}/following"
            params = {'page': page, 'per_page': per_page}

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                page_following = response.json()
                if not page_following:
                    break

                following.extend(page_following)
                logger.info(f"   📄 Página {page}: {len(page_following)} seguidos")
                page += 1
                time.sleep(0.5)
            else:
                logger.error(f"❌ Error obteniendo seguidos: {response.status_code}")
                break

        return following

    def follow_user(self, username: str) -> bool:
        """Seguir a un usuario"""
        if self.dry_run:
            logger.info(f"🧪 [DRY-RUN] Seguiría a @{username}")
            return True

        url = f"{self.base_url}/user/following/{username}"
        response = requests.put(url, headers=self.headers)

        if response.status_code == 204:
            logger.info(f"✅ Ahora sigues a @{username}")
            return True
        logger.error(f"❌ Error siguiendo a @{username}: {response.status_code}")
        return False  # ← BUG FIX: indentación corregida

    def unfollow_user(self, username: str) -> bool:
        """Dejar de seguir a un usuario"""
        if self.dry_run:
            logger.info(f"🧪 [DRY-RUN] Dejaría de seguir a @{username}")
            return True

        url = f"{self.base_url}/user/following/{username}"
        response = requests.delete(url, headers=self.headers)

        if response.status_code == 204:
            logger.info(f"✅ Dejaste de seguir a @{username}")
            return True
        logger.error(f"❌ Error dejando de seguir a @{username}: {response.status_code}")
        return False

    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Obtener información básica de un usuario"""
        url = f"{self.base_url}/users/{username}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        return None

    def should_skip_user(self, user_data: Dict[str, Any]) -> bool:
        """Determinando si saltar un usuario por filtros o whitelist"""
        username = user_data.get('login', '').lower()

        # Whitelist check
        if username in self.whitelist:
            logger.info(f"⏭️  Saltando @{username} (en whitelist)")
            return True

        # Filtros de seguridad
        if user_data.get('followers', 0) > 10000:
            logger.info(f"⏭️  Saltando @{username} (usuario popular)")
            return True

        if user_data.get('type') == 'Organization' and 'github' in username:
            logger.info(f"⏭️  Saltando @{username} (organización GitHub)")
            return True

        return False

    def follow_back_followers(self):
        """Seguir a usuarios que te siguen pero tú no los sigues"""
        logger.info("🚀 Proceso: Seguir a seguidores...")

        followers = self.get_followers()
        following = self.get_following()

        follower_usernames = {user['login'] for user in followers}
        following_usernames = {user['login'] for user in following}
        to_follow_back = follower_usernames - following_usernames

        if not to_follow_back:
            logger.info("✨ Ya sigues a todos tus seguidores!")
            return

        followed_count = 0
        for username in list(to_follow_back)[:self.max_follows_per_run]:
            user_info = self.get_user_info(username)
            if user_info and self.should_skip_user(user_info):
                continue

            if self.follow_user(username):
                followed_count += 1
                time.sleep(self.delay_between_actions)

        logger.info(f"✨ Seguiste a {followed_count} usuarios nuevos.")

    def cleanup_non_followers(self):
        """Dejar de seguir a usuarios que no te siguen de vuelta"""
        logger.info("🧹 Proceso: Limpiar no-seguidores...")

        following = self.get_following()
        followers = self.get_followers()

        follower_usernames = {user['login'].lower() for user in followers}
        following_usernames = {user['login'].lower() for user in following}
        non_followers = following_usernames - follower_usernames

        if not non_followers:
            logger.info("✨ Todos los usuarios que sigues te siguen de vuelta!")
            return

        following_info = {user['login'].lower(): user for user in following}
        unfollowed_count = 0

        for username in list(non_followers)[:self.max_unfollows_per_run]:
            user_inf = following_info.get(username, {})
            if 'followers' not in user_inf:
                user_inf = self.get_user_info(username) or {}

            if self.should_skip_user(user_inf):
                continue

            if self.unfollow_user(username):
                unfollowed_count += 1
                time.sleep(self.delay_between_actions)

        logger.info(f"✨ Dejaste de seguir a {unfollowed_count} usuarios.")

    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas actuales"""
        followers = self.get_followers()
        following = self.get_following()

        follower_usernames = {user['login'].lower() for user in followers}
        following_usernames = {user['login'].lower() for user in following}

        mutual = follower_usernames & following_usernames

        stats = {
            'followers': len(followers),
            'following': len(following),
            'mutual': len(mutual),
            'ratio': len(followers) / max(len(following), 1)
        }

        logger.info(f"📊 Estadísticas: {stats['followers']} seguidores | {stats['following']} siguiendo | Ratio: {stats['ratio']:.2f}")
        return stats

    def run(self, action: str = 'both'):
        """Ejecución principal"""
        if self.dry_run:
            logger.info("🧪 MODO DRY-RUN ACTIVADO: No se realizarán cambios reales.")

        if not self.token or not self.username:
            logger.error("❌ GITHUB_TOKEN o GITHUB_USERNAME no configurados.")
            return

        initial_stats = self.get_statistics()

        if action in ['both', 'follow_back']:
            self.follow_back_followers()
            time.sleep(2)

        if action in ['both', 'cleanup']:
            self.cleanup_non_followers()

        if action != 'stats_only':
            final_stats = self.get_statistics()
            logger.info(f"📈 Cambio: {final_stats['followers'] - initial_stats['followers']:+d} seguidores | {final_stats['following'] - initial_stats['following']:+d} siguiendo")

def main():
    action = os.getenv('AUTOMATION_ACTION', 'both')
    manager = GitHubFollowerManager()
    manager.run(action)

if __name__ == "__main__":
    main()
