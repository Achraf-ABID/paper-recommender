# scripts/fetch_blogs.py

import os
import json
import time
from urllib.parse import urlparse
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- CONFIGURATION ---
BLOG_URLS = [
    "https://medium.com/towards-data-science/a-gentle-introduction-to-retrieval-augmented-generation-35fde2a45b73",
    "https://huggingface.co/blog/gemma",
    "https://aws.amazon.com/fr/blogs/machine-learning/question-answering-using-retrieval-augmented-generation-with-foundation-models-in-amazon-sagemaker-jumpstart/"
]

OUTPUT_DIR = "data/raw/blogs"
DEBUG_DIR = "data/debug"
NORMALIZED_DIR = "data/normalized/blogs"

# --- SÉLECTEURS AMÉLIORÉS AVEC FALLBACKS ---
SELECTORS = {
    "default": {
        "title": ["h1", "h2", "title"],
        "content": ["article", "main", ".post-content", ".entry-content", "div[role='main']"]
    },
    "medium.com": {
        "title": ["h1", "article h1", "h1[class*='title']"],
        "content": [
            "article section",           # Priorité 1
            "article div[class*='postArticle']",  # Priorité 2
            "article",                   # Priorité 3
            "div[class*='postArticle']", # Priorité 4
            "main article",              # Priorité 5
            "section"                    # Priorité 6
        ]
    },
    "towardsdatascience.com": {
        "title": ["h1", "article h1"],
        "content": ["article", "section"]
    },
    "huggingface.co": {
        "title": ["h1", ".blog-post h1"],
        "content": ["article", "main", ".blog-post-content"]
    },
    "aws.amazon.com": {
        "title": ["h1", ".blog-post-title", "article h1", "main h1"],
        "content": [
            "div.blog-post-content",  # Sélecteur original
            "article",                # Fallback 1
            "main article",           # Fallback 2
            "div[id*='main']",        # Fallback 3
            "div.entry-content",      # Fallback 4
            "div.post-content",       # Fallback 5
            "main",                   # Fallback 6
            "div[role='main']"        # Fallback 7
        ]
    }
}

def get_html_and_save_debug(url: str, debug_filepath: str) -> str:
    """
    Utilise Playwright avec stratégie de fallback intelligente.
    """
    print("  [INFO] Lancement du navigateur (Playwright)...")
    html_content = None
    
    # Stratégies de chargement par ordre de préférence
    strategies = [
        {'wait': 'domcontentloaded', 'timeout': 30000, 'name': 'domcontentloaded'},
        {'wait': 'load', 'timeout': 45000, 'name': 'load'},
        {'wait': 'networkidle', 'timeout': 60000, 'name': 'networkidle'}
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        # Essayer chaque stratégie
        for strategy in strategies:
            try:
                print(f"  [INFO] Tentative avec stratégie: {strategy['name']}...")
                page.goto(url, timeout=strategy['timeout'], wait_until=strategy['wait'])
                
                # Attendre le contenu dynamique
                page.wait_for_timeout(3000)
                
                # Scroll pour lazy loading
                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    page.wait_for_timeout(1000)
                except:
                    pass
                
                html_content = page.content()
                
                # Vérifier si on a du contenu valide
                if html_content and len(html_content) > 5000:
                    print(f"  [OK] Contenu récupéré avec {strategy['name']} ({len(html_content)} octets)")
                    break
                else:
                    print(f"  [ATTENTION] Contenu trop court avec {strategy['name']}, essai suivant...")
                    html_content = None
                    
            except PlaywrightTimeoutError:
                print(f"  [TIMEOUT] {strategy['name']} a expiré, essai suivant...")
                continue
            except Exception as e:
                print(f"  [ERREUR] {strategy['name']}: {str(e)[:100]}")
                continue
        
        # Sauvegarder même si on a un contenu partiel
        if html_content:
            try:
                with open(debug_filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"  [DEBUG] HTML sauvegardé : {debug_filepath}")
            except Exception as e:
                print(f"  [ERREUR] Impossible de sauvegarder le debug: {e}")
        
        browser.close()
    
    return html_content

def extract_content_smart(soup: BeautifulSoup, selectors: list) -> tuple:
    """
    Essaie plusieurs sélecteurs et retourne le contenu le plus long trouvé.
    Retourne (content_text, selector_used)
    """
    best_content = ""
    best_selector = None
    
    for selector in selectors:
        try:
            element = soup.select_one(selector)
            if element:
                # Nettoyer les scripts et styles
                for script in element(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                
                content = element.get_text(separator='\n\n', strip=True)
                
                # Garder le contenu le plus long
                if len(content) > len(best_content):
                    best_content = content
                    best_selector = selector
                    
        except Exception as e:
            continue
    
    return best_content, best_selector

def extract_title_smart(soup: BeautifulSoup, selectors: list) -> tuple:
    """
    Essaie plusieurs sélecteurs pour le titre.
    Retourne (title, selector_used)
    """
    for selector in selectors:
        try:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 5:  # Au moins 5 caractères
                    return title, selector
        except Exception as e:
            continue
    
    return None, None

def extract_metadata(soup: BeautifulSoup, url: str, title: str, content: str) -> dict:
    """
    ÉTAPE 3: Extraction et normalisation des métadonnées.
    """
    metadata = {
        "id": None,
        "title": title,
        "authors": [],
        "date": None,
        "doi": None,
        "source": urlparse(url).netloc,
        "tags": [],
        "url": url,
        "raw_text": content,
        "abstract": None,
        "first_paragraph": None,
        "retrieved_at": datetime.now(datetime.UTC).isoformat() if hasattr(datetime, 'UTC') else datetime.utcnow().isoformat(),
        "content_type": "blog",
        "content_length": len(content)
    }

    metadata["id"] = f"blog_{abs(hash(url))}"

    # Extraction des auteurs
    author_selectors = [
        ('meta', {'name': 'author'}),
        ('meta', {'property': 'article:author'}),
        ('meta', {'name': 'parsely-author'}),
        ('span', {'class': 'author'}),
        ('a', {'rel': 'author'})
    ]
    
    for tag_name, attrs in author_selectors:
        author_element = soup.find(tag_name, attrs=attrs)
        if author_element:
            author = author_element.get('content') or author_element.get_text(strip=True)
            if author:
                metadata["authors"].append(author)
                break

    # Extraction de la date
    date_selectors = [
        ('meta', {'property': 'article:published_time'}),
        ('meta', {'name': 'publication_date'}),
        ('meta', {'name': 'date'}),
        ('time', {'datetime': True}),
        ('time', {})
    ]
    
    for tag_name, attrs in date_selectors:
        date_element = soup.find(tag_name, attrs=attrs)
        if date_element:
            date_str = date_element.get('content') or date_element.get('datetime') or date_element.get_text(strip=True)
            if date_str:
                metadata["date"] = date_str
                break

    # Extraction des tags
    keywords_meta = soup.find('meta', attrs={'name': 'keywords'}) or \
                    soup.find('meta', attrs={'property': 'article:tag'})
    if keywords_meta and keywords_meta.get('content'):
        metadata["tags"] = [tag.strip() for tag in keywords_meta.get('content').split(',')]

    # Premier paragraphe
    if content and len(content) > 100:
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 50]
        if paragraphs:
            metadata["first_paragraph"] = paragraphs[0][:500]

    # Abstract depuis meta description
    desc_selectors = [
        ('meta', {'name': 'description'}),
        ('meta', {'property': 'og:description'}),
        ('meta', {'name': 'twitter:description'})
    ]
    
    for tag_name, attrs in desc_selectors:
        desc_element = soup.find(tag_name, attrs=attrs)
        if desc_element and desc_element.get('content'):
            metadata["abstract"] = desc_element.get('content')
            break

    return metadata

def save_normalized_data(metadata: dict, raw_html: str):
    """
    ÉTAPE 3: Sauvegarde les données normalisées et le HTML brut.
    """
    os.makedirs(NORMALIZED_DIR, exist_ok=True)
    
    metadata_filename = f"{metadata['id']}_metadata.json"
    metadata_filepath = os.path.join(NORMALIZED_DIR, metadata_filename)
    
    with open(metadata_filepath, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
    
    print(f"  [ÉTAPE 3] Métadonnées normalisées : {metadata_filepath}")
    
    raw_filename = f"{metadata['id']}_raw.html"
    raw_filepath = os.path.join(NORMALIZED_DIR, raw_filename)
    
    provenance = {
        "source_url": metadata['url'],
        "crawl_timestamp": metadata['retrieved_at'],
        "source_type": "blog",
        "raw_file": raw_filename
    }
    
    with open(raw_filepath, 'w', encoding='utf-8') as f:
        f.write(f"<!-- PROVENANCE: {json.dumps(provenance)} -->\n")
        f.write(raw_html)
    
    print(f"  [ÉTAPE 3] HTML brut sauvegardé : {raw_filepath}")

def fetch_blog_posts():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DEBUG_DIR, exist_ok=True)
    os.makedirs(NORMALIZED_DIR, exist_ok=True)

    all_metadata = []

    for url in BLOG_URLS:
        print(f"\n{'='*60}")
        print(f"Traitement de l'URL : {url}")
        print('='*60)
        
        domain = urlparse(url).netloc
        debug_filename = f"debug_{domain.replace('.', '_')}.html"
        debug_filepath = os.path.join(DEBUG_DIR, debug_filename)

        html_content = get_html_and_save_debug(url, debug_filepath)

        if not html_content:
            print(f"  [ÉCHEC] Impossible de récupérer le HTML. Passage au suivant.")
            continue

        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Obtenir les sélecteurs pour ce domaine
        site_selectors = SELECTORS.get(domain, SELECTORS["default"])
        
        # Extraction intelligente du titre
        print(f"  [INFO] Extraction du titre...")
        title, title_selector = extract_title_smart(soup, site_selectors["title"])
        if not title:
            title = "Titre non trouvé"
            print(f"  [ATTENTION] Titre non trouvé")
        else:
            print(f"  [OK] Titre trouvé avec sélecteur: {title_selector}")
            print(f"       Titre: {title[:80]}...")

        # Extraction intelligente du contenu
        print(f"  [INFO] Extraction du contenu...")
        content, content_selector = extract_content_smart(soup, site_selectors["content"])
        
        if not content or len(content) < 100:
            content = "Contenu non trouvé"
            print(f"  [ERREUR] Contenu non trouvé ou trop court")
            print(f"  [CONSEIL] Vérifiez le fichier de débogage: {debug_filepath}")
        else:
            print(f"  [OK] Contenu trouvé avec sélecteur: {content_selector}")
            print(f"       Longueur: {len(content)} caractères")
            print(f"       Aperçu: {content[:150]}...")
        
        # Sauvegarde format original
        path = urlparse(url).path.replace('/', '_').strip('_')
        filename = f"{domain}_{path}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        basic_data = {
            "url": url, 
            "title": title, 
            "content": content,
            "selector_used": {
                "title": title_selector,
                "content": content_selector
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(basic_data, f, ensure_ascii=False, indent=4)
        
        print(f"  [OK] JSON basique sauvegardé : {filepath}")

        # ÉTAPE 3: Extraction et normalisation
        if content != "Contenu non trouvé":
            print(f"  [ÉTAPE 3] Extraction des métadonnées...")
            metadata = extract_metadata(soup, url, title, content)
            save_normalized_data(metadata, html_content)
            all_metadata.append(metadata)
        else:
            print(f"  [ÉTAPE 3] Ignoré - contenu non trouvé")

        time.sleep(2)

    # Export JSON plat
    if all_metadata:
        export_filepath = os.path.join(NORMALIZED_DIR, "all_blogs_metadata.json")
        with open(export_filepath, 'w', encoding='utf-8') as f:
            json.dump(all_metadata, f, ensure_ascii=False, indent=4)
        
        print(f"\n{'='*60}")
        print(f"[ÉTAPE 3] Export JSON plat créé : {export_filepath}")
        print(f"Total de blogs traités : {len(all_metadata)}")
        print('='*60)
    
    print("\n✅ Collecte des données de blogs terminée.")

if __name__ == "__main__":
    fetch_blog_posts()