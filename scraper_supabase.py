import time
import re
import os
import httpx
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
SUPABASE_URL = "https://ewhcinmihogmusmldeds.supabase.co"
SUPABASE_KEY = "sb_publishable_X7hVXnbUmyJGL0JbO0jpbw_Gw1dznI2"
MSK_BASE_URL = "https://www.mskcc.org/cancer-care/integrative-medicine/herbs"

# Inicializar Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def setup_driver():
    options = Options()
    # options.add_argument("--headless")  # Quitar comentario para modo oculto
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--lang=es")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_herb_links():
    print("Obteniendo lista de hierbas desde MSK...")
    r = httpx.get("https://www.mskcc.org/cancer-care/diagnosis-treatment/symptom-management/integrative-medicine/herbs")
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    # Buscar todos los enlaces que contienen la ruta de hierbas
    for a in soup.find_all("a", href=re.compile(r"/cancer-care/integrative-medicine/herbs/")):
        href = a['href']
        slug = href.split('/')[-1]
        if slug and slug not in ["herbs", "search"]:
            links.append(slug)
    return sorted(list(set(links)))

def scrape_translated_herb(slug, driver):
    url = f"{MSK_BASE_URL}/{slug}"
    # Usar el visor de Google Translate para traducir la página completa
    translate_url = f"https://translate.google.com/translate?sl=en&tl=es&u={url}"
    
    print(f"Traduciendo y extrayendo: {slug}...")
    driver.get(translate_url)
    
    # Esperar a que la página cargue y el iframe de traducción esté listo
    time.sleep(5) 
    
    # Intentar cambiar al iframe de Google Translate si existe
    try:
        driver.switch_to.frame("c") # 'c' es el ID común del iframe de contenido traducido
    except:
        pass # A veces no es necesario o el ID cambia

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Lógica de extracción (basada en nutriken_engine.py)
    content = soup.get_text(separator="\n")
    
    def _extract(pattern, text, flags=re.DOTALL, limit=3000):
        m = re.search(pattern, text, flags)
        return m.group(1).strip()[:limit] if m else ""

    def _list(pattern, text, limit=20):
        m = re.search(pattern, text, re.DOTALL)
        if not m: return []
        return [l.strip('- •*').strip() for l in m.group(1).split('\n')
                if l.strip() and len(l.strip()) > 5][:limit]

    # Ajustar patrones para buscar los títulos traducidos
    herb = {
        "slug": slug,
        "name": _extract(r'##\s*(.*?)(?=\n)', content).title() or slug.replace("-"," ").title(),
        "scientific_name": _extract(r'(?:Nombre científico|Scientific Name)\s*\n+([^\n]+)', content),
        "url": url,
        "what_is_it": _extract(r'(?:¿Qué es\?|What is it\?)\s*\n+(.*?)(?=¿Cuáles son|What are)', content),
        "clinical_summary": _extract(r'(?:Resumen clínico|Clinical Summary)\s*\n+(.*?)(?=Uso propuesto|Mecanismo|Purported|Mechanism)', content),
        "mechanism_of_action": _extract(r'(?:Mecanismo de acción|Mechanism of Action)\s*\n+(.*?)(?=Farmacología|Efectos|Pharmacology|Adverse)', content),
        "adverse_reactions": _extract(r'(?:Reacciones adversas|Adverse Reactions)\s*\n+(.*?)(?=Interacciones|Dosificación|Herb-Drug|Dosage)', content),
        "contraindications": _extract(r'(?:Contraindicaciones|Contraindications)\s*\n+(.*?)(?=Adverso|Referencias|Adverse|References)', content),
        "dosage": _extract(r'(?:Dosificación|Dosage)\s*\n+(.*?)(?=Referencias|References)', content),
        "benefits": _list(r'(?:¿Cuáles son los usos y beneficios potenciales\?|What are the potential uses and benefits\?)\s*\n+(.*?)(?=¿Cuáles son los efectos secundarios|What are the side effects)', content),
        "drug_interactions": _list(r'(?:Interacciones hierba-fármaco|Herb-Drug Interactions)\s*\n+(.*?)(?=Dosificación|Referencias|Dosage|References)', content),
        "side_effects": _list(r'(?:¿Cuáles son los efectos secundarios\?|What are the side effects\?)\s*\n+(.*?)(?=¿Qué más necesito saber|What else do I need)', content),
        "warnings": _list(r'(?:¿Qué más necesito saber\?|What else do I need to know\?)\s*\n+(.*?)(?=Para profesionales|##)', content)
    }
    
    return herb

def main():
    slugs = get_herb_links()
    print(f"Total de hierbas encontradas: {len(slugs)}")
    
    driver = setup_driver()
    
    try:
        for slug in slugs:
            # Verificar si ya existe en Supabase para poder reanudar si falla
            existing = supabase.table("msk_herbs").select("slug").eq("slug", slug).execute()
            if existing.data:
                print(f"Saltando {slug} (ya existe en Supabase)")
                continue
                
            try:
                data = scrape_translated_herb(slug, driver)
                
                # Insertar en Supabase
                res = supabase.table("msk_herbs").insert(data).execute()
                print(f"✅ Subido con éxito: {data['name']}")
                
                # Breve pausa para no saturar
                time.sleep(2)
            except Exception as e:
                print(f"❌ Error procesando {slug}: {e}")
                
    finally:
        driver.quit()
        print("Proceso finalizado.")

if __name__ == "__main__":
    main()
