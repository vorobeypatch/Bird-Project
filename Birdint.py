# Проект BirdOSINT by @apolovosint
import os
import sys
import time
import json
import re
import smtplib
import dns.resolver
import requests
import platform
import subprocess
import pickle
import hashlib
from collections import defaultdict
from urllib.parse import urlparse
from datetime import datetime
from threading import Thread
from queue import Queue

try:
    from PIL import Image
except ImportError:
    print("Установка библиотек...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "requests", "dnspython"])
    print("Готово. Запустите скрипт снова.")
    sys.exit(0)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(BASE_DIR, "data", "images", "main.png")
DATA_DIR = os.path.join(BASE_DIR, "data")
AI_KNOWLEDGE_FILE = os.path.join(DATA_DIR, "ai_knowledge.pkl")
API_KEY_WHOIS = "ok_f22649a760a8749697c7c46b6953535f"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(DATA_DIR, "images"), exist_ok=True)

class OSINTAI:
    def __init__(self):
        self.knowledge = self.load_knowledge()
        self.learning_queue = Queue()
        self.start_learning_worker()
    
    def load_knowledge(self):
        if os.path.exists(AI_KNOWLEDGE_FILE):
            try:
                with open(AI_KNOWLEDGE_FILE, 'rb') as f:
                    return pickle.load(f)
            except:
                return self.init_knowledge()
        else:
            return self.init_knowledge()
    
    def init_knowledge(self):
        return {
            "platforms": {
                "social": [
                    {"name": "Twitter", "url": "https://twitter.com/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Instagram", "url": "https://instagram.com/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Facebook", "url": "https://facebook.com/{}", "success_count": 0, "fail_count": 0},
                    {"name": "TikTok", "url": "https://tiktok.com/@{}", "success_count": 0, "fail_count": 0},
                    {"name": "YouTube", "url": "https://youtube.com/@{}", "success_count": 0, "fail_count": 0},
                    {"name": "Reddit", "url": "https://reddit.com/user/{}", "success_count": 0, "fail_count": 0},
                    {"name": "LinkedIn", "url": "https://linkedin.com/in/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Pinterest", "url": "https://pinterest.com/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Tumblr", "url": "https://{}.tumblr.com", "success_count": 0, "fail_count": 0},
                    {"name": "Snapchat", "url": "https://snapchat.com/add/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Telegram", "url": "https://t.me/{}", "success_count": 0, "fail_count": 0},
                    {"name": "VK", "url": "https://vk.com/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Twitch", "url": "https://twitch.tv/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Discord", "url": "https://discord.com/users/{}", "success_count": 0, "fail_count": 0},
                ],
                "dev": [
                    {"name": "GitHub", "url": "https://github.com/{}", "success_count": 0, "fail_count": 0},
                    {"name": "GitLab", "url": "https://gitlab.com/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Stack Overflow", "url": "https://stackoverflow.com/users/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Dev.to", "url": "https://dev.to/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Medium", "url": "https://medium.com/@{}", "success_count": 0, "fail_count": 0},
                    {"name": "HackerOne", "url": "https://hackerone.com/{}", "success_count": 0, "fail_count": 0},
                ],
                "gaming": [
                    {"name": "Steam", "url": "https://steamcommunity.com/id/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Epic Games", "url": "https://epicgames.com/id/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Xbox", "url": "https://xbox.com/player/{}", "success_count": 0, "fail_count": 0},
                    {"name": "PlayStation", "url": "https://psnprofiles.com/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Roblox", "url": "https://roblox.com/user.aspx?username={}", "success_count": 0, "fail_count": 0},
                ],
                "forums": [
                    {"name": "Quora", "url": "https://quora.com/profile/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Product Hunt", "url": "https://producthunt.com/@{}", "success_count": 0, "fail_count": 0},
                    {"name": "Behance", "url": "https://behance.net/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Dribbble", "url": "https://dribbble.com/{}", "success_count": 0, "fail_count": 0},
                ],
                "other": [
                    {"name": "Spotify", "url": "https://open.spotify.com/user/{}", "success_count": 0, "fail_count": 0},
                    {"name": "SoundCloud", "url": "https://soundcloud.com/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Last.fm", "url": "https://last.fm/user/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Patreon", "url": "https://patreon.com/{}", "success_count": 0, "fail_count": 0},
                    {"name": "About.me", "url": "https://about.me/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Imgur", "url": "https://imgur.com/user/{}", "success_count": 0, "fail_count": 0},
                    {"name": "Keybase", "url": "https://keybase.io/{}", "success_count": 0, "fail_count": 0},
                ]
            },
            "not_found_patterns": [
                "not found", "page not found", "does not exist", "404",
                "не найден", "не существует", "profile not available",
                "user not found", "no such user", "account suspended",
                "this profile doesn't exist", "page doesn't exist",
                "couldn't find", "sorry, this page isn't available",
                "the link you followed may be broken", "content isn't available",
                "this account doesn't exist", "user does not exist"
            ],
            "discovered_sites": [],
            "search_history": [],
            "username_patterns": []
        }
    
    def save_knowledge(self):
        try:
            with open(AI_KNOWLEDGE_FILE, 'wb') as f:
                pickle.dump(self.knowledge, f)
        except:
            pass
    
    def start_learning_worker(self):
        def worker():
            while True:
                try:
                    item = self.learning_queue.get(timeout=1)
                    self.process_learning_item(item)
                except:
                    time.sleep(5)
        
        thread = Thread(target=worker, daemon=True)
        thread.start()
    
    def process_learning_item(self, item):
        if item["type"] == "success":
            platform_name = item["platform"]
            for category in self.knowledge["platforms"]:
                for p in self.knowledge["platforms"][category]:
                    if p["name"] == platform_name:
                        p["success_count"] += 1
                        break
        
        elif item["type"] == "fail":
            platform_name = item["platform"]
            for category in self.knowledge["platforms"]:
                for p in self.knowledge["platforms"][category]:
                    if p["name"] == platform_name:
                        p["fail_count"] += 1
                        break
        
        elif item["type"] == "discover":
            if item["url"] not in self.knowledge["discovered_sites"]:
                self.knowledge["discovered_sites"].append(item["url"])
        
        elif item["type"] == "pattern":
            if item["pattern"] not in self.knowledge["username_patterns"]:
                self.knowledge["username_patterns"].append(item["pattern"])
        
        self.save_knowledge()
    
    def check_account_exists(self, platform, url, username):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
            
            if response.status_code == 200:
                page_text = response.text.lower()
                
                for pattern in self.knowledge["not_found_patterns"]:
                    if pattern in page_text:
                        self.learning_queue.put({"type": "fail", "platform": platform})
                        return False, None
                
                title_patterns = ["404", "error", "not found"]
                if any(p in page_text for p in title_patterns):
                    self.learning_queue.put({"type": "fail", "platform": platform})
                    return False, None
                
                if username.lower() not in page_text and len(username) > 3:
                    if "profile" in page_text or "user" in page_text:
                        pass
                
                self.learning_queue.put({"type": "success", "platform": platform})
                self.learning_queue.put({"type": "discover", "url": url})
                
                mentions = re.findall(r'@(\w+)', response.text)
                for mention in mentions[:5]:
                    if len(mention) > 2:
                        self.learning_queue.put({"type": "pattern", "pattern": mention})
                
                return True, response.text
            else:
                self.learning_queue.put({"type": "fail", "platform": platform})
                return False, None
                
        except requests.exceptions.Timeout:
            return False, None
        except requests.exceptions.ConnectionError:
            return False, None
        except Exception:
            return False, None
    
    def extract_profile_info(self, html, username):
        info = {
            "mentions": [],
            "hashtags": [],
            "description": "",
            "followers": None,
            "following": None,
            "posts": None
        }
        
        try:
            mentions = re.findall(r'@(\w+)', html)
            info["mentions"] = list(set([m for m in mentions if len(m) > 2]))[:15]
            
            hashtags = re.findall(r'#(\w+)', html)
            info["hashtags"] = list(set([h for h in hashtags if len(h) > 2]))[:15]
            
            desc_patterns = [
                r'<meta[^>]*name="description"[^>]*content="([^"]*)"',
                r'<meta[^>]*property="og:description"[^>]*content="([^"]*)"',
                r'<div[^>]*class="[^"]*bio[^"]*"[^>]*>(.*?)</div>',
                r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>'
            ]
            
            for pattern in desc_patterns:
                desc = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if desc:
                    clean = re.sub('<[^<]+?>', '', desc.group(1))
                    info["description"] = clean[:200]
                    break
            
            follower_patterns = [
                r'(\d+[,.]?\d*)\s*(?:followers|подписчиков)',
                r'followers["\']?\s*:\s*["\']?(\d+)',
                r'подписчиков["\']?\s*:\s*["\']?(\d+)'
            ]
            
            for pattern in follower_patterns:
                followers = re.search(pattern, html, re.IGNORECASE)
                if followers:
                    info["followers"] = followers.group(1).replace(',', '').replace('.', '')
                    break
            
        except:
            pass
        
        return info
    
    def generate_ai_analysis(self, username, found_accounts, all_info):
        analysis = []
        analysis.append("")
        analysis.append("=" * 70)
        analysis.append(f"ОБЩИЙ РЕЗУЛЬТАТ И АНАЛИЗ:")
        analysis.append("=" * 70)
        
        if found_accounts:
            total = len(found_accounts)
            analysis.append(f"\n📊 Найдено аккаунтов: {total}")
            
            platforms_by_type = {"social": 0, "dev": 0, "gaming": 0, "forums": 0, "other": 0}
            for platform, _, _ in found_accounts:
                for cat_name, cat_platforms in self.knowledge["platforms"].items():
                    if any(p["name"] == platform for p in cat_platforms):
                        platforms_by_type[cat_name] += 1
                        break
            
            analysis.append("\n📋 Распределение по категориям:")
            for cat, count in platforms_by_type.items():
                if count > 0:
                    analysis.append(f"  • {cat.capitalize()}: {count}")
            
            all_mentions = []
            all_hashtags = []
            for info in all_info:
                all_mentions.extend(info.get("mentions", []))
                all_hashtags.extend(info.get("hashtags", []))
            
            if all_mentions:
                unique_mentions = list(set(all_mentions))[:10]
                analysis.append(f"\n👥 Упоминания других пользователей:")
                analysis.append(f"  {', '.join(['@' + m for m in unique_mentions])}")
            
            if all_hashtags:
                unique_tags = list(set(all_hashtags))[:10]
                analysis.append(f"\n🏷️ Используемые хэштеги:")
                analysis.append(f"  {', '.join(['#' + t for t in unique_tags])}")
            
            descriptions = [info.get("description", "") for info in all_info if info.get("description")]
            if descriptions:
                analysis.append(f"\n📝 Описания профилей:")
                for desc in descriptions[:3]:
                    if desc:
                        analysis.append(f"  • {desc[:100]}...")
            
            success_rate = 0
            for platform, _, _ in found_accounts:
                for cat in self.knowledge["platforms"].values():
                    for p in cat:
                        if p["name"] == platform:
                            total = p["success_count"] + p["fail_count"]
                            if total > 0:
                                rate = (p["success_count"] / total) * 100
                                success_rate += rate
            
            if total > 0:
                avg_rate = success_rate / total
                analysis.append(f"\n📈 Средняя достоверность: {avg_rate:.1f}%")
            
            if total > 10:
                analysis.append(f"\n🧠 Мнение ИИ: Пользователь очень активен в интернете")
            elif total > 5:
                analysis.append(f"\n🧠 Мнение ИИ: Пользователь умеренно активен")
            elif total > 2:
                analysis.append(f"\n🧠 Мнение ИИ: Пользователь имеет ограниченное присутствие")
            else:
                analysis.append(f"\n🧠 Мнение ИИ: Пользователь ведет скрытую активность")
            
            if all_mentions:
                analysis.append(f"🧠 Мнение ИИ: Активно взаимодействует с другими пользователями")
            
            if all_hashtags:
                analysis.append(f"🧠 Мнение ИИ: Использует тематические хэштеги для категоризации")
            
        else:
            analysis.append(f"\n❌ Аккаунты с username '{username}' не обнаружены")
            analysis.append(f"\n🧠 Мнение ИИ: Возможные причины:")
            analysis.append(f"  • Username используется редко")
            analysis.append(f"  • Пользователь предпочитает другие никнеймы")
            analysis.append(f"  • Аккаунты были удалены")
            analysis.append(f"\n💡 Рекомендация: Попробуйте варианты с цифрами или символами")
        
        return "\n".join(analysis)

def animate_text(text):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(0.03)
    print()

def show_banner():
    try:
        if os.path.exists(IMAGE_PATH):
            img = Image.open(IMAGE_PATH)
            img.show()
            time.sleep(3)
        else:
            print("""
╔═══════════════════════════════════════════════════════════════╗
║                    BIRD PROJECT OSINT                         ║
║         Internet Intelligence & Automated Collection          ║
╚═══════════════════════════════════════════════════════════════╝
            """)
    except:
        pass

def main_menu():
    os.system('cls' if platform.system() == 'Windows' else 'clear')
    
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                    BIRD PROJECT OSINT                         ║")
    print("║                       v2.0 - AI Enhanced                      ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print("")
    print("┌───────────────────────────────────────────────────────────────┐")
    print("│                         ГЛАВНОЕ МЕНЮ                          │")
    print("├───────────────────────────────────────────────────────────────┤")
    print("│  1. Username                           2. Email               │")
    print("│  3. IP-address                         4. Domain              │")
    print("│  0. Exit                                                     │")
    print("└───────────────────────────────────────────────────────────────┘")
    print("")
    print("→ Выберите функцию: ", end="")
    return input().strip()

def search_username(ai):
    print("\n> Отправьте username: ", end="")
    username = input().strip()
    
    if not username:
        return
    
    print("\nСбор и анализ информации...\n")
    
    found_accounts = []
    all_profile_info = []
    
    total_platforms = sum(len(cat) for cat in ai.knowledge["platforms"].values())
    checked = 0
    
    for category, platforms in ai.knowledge["platforms"].items():
        for platform in platforms:
            checked += 1
            percent = (checked / total_platforms) * 100
            print(f"\rПрогресс: [{('=' * int(percent // 2)).ljust(50)}] {percent:.1f}%", end="")
            
            url = platform["url"].format(username)
            exists, html = ai.check_account_exists(platform["name"], url, username)
            
            if exists:
                profile_info = ai.extract_profile_info(html, username)
                found_accounts.append((platform["name"], url, profile_info))
                all_profile_info.append(profile_info)
            
            time.sleep(0.3)
    
    print("\n")
    print("=" * 70)
    print(f"Найдено информация о username: {username}")
    print("=" * 70)
    print("")
    
    if found_accounts:
        for platform, url, info in found_accounts:
            print(f"[+] {platform}: {url}")
            if info.get("followers"):
                print(f"    Подписчики: {info['followers']}")
    else:
        print("Аккаунты не найдены")
    
    all_mentions = []
    all_hashtags = []
    for info in all_profile_info:
        all_mentions.extend(info.get("mentions", []))
        all_hashtags.extend(info.get("hashtags", []))
    
    if all_mentions or all_hashtags:
        print("")
        print("Упоминание в сети:")
        if all_mentions:
            unique_mentions = list(set(all_mentions))[:10]
            print("  Упоминания: " + ", ".join(['@' + m for m in unique_mentions]))
        if all_hashtags:
            unique_tags = list(set(all_hashtags))[:10]
            print("  Теги: " + ", ".join(['#' + t for t in unique_tags]))
    
    print(ai.generate_ai_analysis(username, found_accounts, all_profile_info))
    
    print("")
    print("Нажмите на Enter чтобы вернуться назад...", end="")
    input()

def search_email():
    print("\n> Отправьте email address: ", end="")
    email = input().strip()
    
    if not email or '@' not in email:
        print("Неверный формат email")
        print("\nНажмите на Enter чтобы вернуться назад...", end="")
        input()
        return
    
    domain = email.split('@')[1]
    
    try:
        records = dns.resolver.resolve(domain, 'MX')
        mx = str(records[0].exchange)
        
        server = smtplib.SMTP(timeout=10)
        server.connect(mx)
        server.helo(server.local_hostname)
        server.mail('check@example.com')
        code, message = server.rcpt(email)
        server.quit()
        
        if code == 250:
            print("✅ Email существует")
            print("\n(Результаты SMTP запроса)")
            print(f"  MX сервер: {mx}")
            print(f"  Статус: Доставка возможна")
            print(f"  Код ответа: {code}")
        else:
            print("❌ Такого email адреса не существует")
            print("\nНажмите на Enter чтобы вернуться назад...", end="")
            input()
            return
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\nНажмите на Enter чтобы вернуться назад...", end="")
        input()
        return
    
    print("\nРезультаты от LeakCheck:")
    
    try:
        r = requests.get("https://leakcheck.io/api/public", params={"check": email}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("success") and data.get("found", 0) > 0:
                print(f"⚠️ Найдено утечек: {data['found']}")
                if "fields" in data:
                    print("Поля:")
                    for field in data["fields"]:
                        print(f"  • {field}")
                if "sources" in data:
                    print("Источники:")
                    for src in data["sources"]:
                        print(f"  • {src['name']} ({src.get('date', 'N/A')})")
            else:
                print("✅ Утечек не найдено")
        else:
            print("Не удалось проверить утечки")
    except:
        print("Ошибка при проверке утечек")
    
    print("\nНажмите на Enter чтобы вернуться назад...", end="")
    input()

def search_ip():
    print("\n> Отправьте IP-address: ", end="")
    ip = input().strip()
    
    if not ip:
        return
    
    print("Получение данных...")
    
    try:
        r = requests.get(f"http://ipwho.is/{ip}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("success"):
                print("\nРезультаты:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(f"Ошибка: {data.get('message', 'Unknown')}")
        else:
            print(f"HTTP ошибка: {r.status_code}")
    except Exception as e:
        print(f"Ошибка: {e}")
    
    print("\nНажмите на Enter чтобы вернуться назад...", end="")
    input()

def search_domain():
    print("\n> Отправьте domain: ", end="")
    domain = input().strip()
    
    if not domain:
        return
    
    domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
    
    print("Получение WHOIS информации...")
    
    try:
        r = requests.get(
            "https://whois-api.omkar.cloud/whois",
            params={"domain": domain},
            headers={"API-Key": API_KEY_WHOIS},
            timeout=10
        )
        
        if r.status_code == 200:
            data = r.json()
            print("\nРезультаты WHOIS:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"Ошибка: {r.status_code}")
    except Exception as e:
        print(f"Ошибка: {e}")
    
    print("\nНажмите на Enter чтобы вернуться назад...", end="")
    input()

def main():
    animate_text("Bird Project is an OSINT project based on internet intelligence, automated collection of information about objects by analyzing the source data.")
    time.sleep(5)
    
    show_banner()
    time.sleep(2)
    
    ai = OSINTAI()
    
    while True:
        choice = main_menu()
        
        if choice == "1":
            search_username(ai)
        elif choice == "2":
            search_email()
        elif choice == "3":
            search_ip()
        elif choice == "4":
            search_domain()
        elif choice == "0":
            print("Выход...")
            sys.exit(0)
        else:
            print("Неверный выбор")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрограмма остановлена")
        sys.exit(0)
