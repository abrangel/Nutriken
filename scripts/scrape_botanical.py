"""
Scraper botánico masivo (JOSS-compatible, fuente ABIERTA CC0: LOTUS naturalproducts.net).
Para una lista curada de plantas medicinales/nutricionales, consulta LOTUS y guarda sus
fitoquímicos (SMILES, lotus_id, wikidata) en local_db/botanical_index.json.
LOTUS es CC0 (dominio público) → redistribuible en un repo open-source.
Ejecutar:  python scripts/scrape_botanical.py [limite_plantas]
Reanudable: salta plantas ya hechas; guarda cada 15.
"""
import os, sys, json, time, requests

LOTUS = "https://lotus.naturalproducts.net/api/search/simple"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "local_db", "botanical_index.json")
PER_PLANT = 40  # compuestos guardados por planta

PLANTS = [
 "Curcuma longa","Zingiber officinale","Allium sativum","Camellia sinensis","Panax ginseng",
 "Withania somnifera","Silybum marianum","Ginkgo biloba","Vitis vinifera","Glycine max",
 "Rosmarinus officinalis","Ocimum sanctum","Ocimum basilicum","Cinnamomum verum","Cinnamomum cassia",
 "Trigonella foenum-graecum","Berberis vulgaris","Coptis chinensis","Hydrastis canadensis","Boswellia serrata",
 "Ganoderma lucidum","Hericium erinaceus","Cordyceps militaris","Trametes versicolor","Lentinula edodes",
 "Astragalus membranaceus","Rhodiola rosea","Eleutherococcus senticosus","Schisandra chinensis","Bacopa monnieri",
 "Centella asiatica","Serenoa repens","Urtica dioica","Taraxacum officinale","Cynara scolymus",
 "Matricaria chamomilla","Melissa officinalis","Valeriana officinalis","Passiflora incarnata","Lavandula angustifolia",
 "Hypericum perforatum","Echinacea purpurea","Sambucus nigra","Andrographis paniculata","Uncaria tomentosa",
 "Curcuma zedoaria","Piper nigrum","Piper longum","Capsicum annuum","Allium cepa",
 "Brassica oleracea","Raphanus sativus","Moringa oleifera","Punica granatum","Citrus bergamia",
 "Citrus aurantium","Citrus limon","Olea europaea","Linum usitatissimum","Salvia officinalis",
 "Salvia miltiorrhiza","Mentha piperita","Thymus vulgaris","Origanum vulgare","Eucalyptus globulus",
 "Aloe vera","Calendula officinalis","Arnica montana","Ginkgo biloba","Crataegus monogyna",
 "Hibiscus sabdariffa","Theobroma cacao","Coffea arabica","Paullinia cupana","Ilex paraguariensis",
 "Garcinia cambogia","Cannabis sativa","Humulus lupulus","Glycyrrhiza glabra","Zingiber zerumbet",
 "Nigella sativa","Foeniculum vulgare","Coriandrum sativum","Cuminum cyminum","Elettaria cardamomum",
 "Syzygium aromaticum","Myristica fragrans","Crocus sativus","Vaccinium myrtillus","Vaccinium macrocarpon",
 "Rubus idaeus","Fragaria vesca","Prunus avium","Malus domestica","Beta vulgaris",
 "Spinacia oleracea","Daucus carota","Solanum lycopersicum","Capsicum frutescens","Momordica charantia",
 "Gymnema sylvestre","Cinnamomum camphora","Pelargonium sidoides","Plantago ovata","Plantago major",
 "Aesculus hippocastanum","Ruscus aculeatus","Vitex agnus-castus","Angelica sinensis","Cimicifuga racemosa",
 "Dioscorea villosa","Tribulus terrestris","Epimedium sagittatum","Lepidium meyenii","Eurycoma longifolia",
 "Mucuna pruriens","Griffonia simplicifolia","Rauvolfia serpentina","Catharanthus roseus","Taxus baccata",
 "Artemisia annua","Artemisia absinthium","Tanacetum parthenium","Cichorium intybus","Inula helenium",
 "Arctium lappa","Rheum palmatum","Cassia angustifolia","Aloe ferox","Frangula alnus",
 "Salix alba","Filipendula ulmaria","Harpagophytum procumbens","Curcuma aromatica","Alpinia galanga",
 "Kaempferia galanga","Acorus calamus","Valeriana jatamansi","Nardostachys jatamansi","Bacopa floribunda",
 "Centella erecta","Terminalia chebula","Terminalia arjuna","Emblica officinalis","Phyllanthus niruri",
 "Azadirachta indica","Tinospora cordifolia","Asparagus racemosus","Bacopa caroliniana","Ocimum gratissimum",
 "Rosa canina","Rosa damascena","Jasminum officinale","Chrysanthemum morifolium","Lonicera japonica",
 "Scutellaria baicalensis","Paeonia lactiflora","Angelica archangelica","Levisticum officinale","Petroselinum crispum",
 "Apium graveolens","Anethum graveolens","Carum carvi","Pimpinella anisum","Illicium verum",
 "Vanilla planifolia","Stevia rebaudiana","Aspalathus linearis","Cyamopsis tetragonoloba","Avena sativa",
 "Hordeum vulgare","Triticum aestivum","Oryza sativa","Zea mays","Sesamum indicum",
 "Helianthus annuus","Cucurbita pepo","Persea americana","Cocos nucifera","Olea europaea",
 "Juglans regia","Prunus dulcis","Anacardium occidentale","Pistacia vera","Corylus avellana",
 "Theobroma bicolor","Coffea canephora","Camellia oleifera","Ilex guayusa","Cola acuminata",
 "Ephedra sinica","Pausinystalia johimbe","Citrus reticulata","Citrus paradisi","Citrus sinensis",
]


def fetch_plant(name):
    try:
        r = requests.get(LOTUS, params={"query": name, "limit": PER_PLANT}, timeout=30)
        if r.status_code != 200:
            return None
        d = r.json()
        nps = d.get("naturalProducts", [])
        comps = []
        for np in nps:
            comps.append({k: np.get(k) for k in ("lotus_id", "smiles", "inchikey", "wikidata_id") if np.get(k)})
        return {"plant": name, "compound_count": len(nps), "compounds": comps,
                "lotus_query": f"https://lotus.naturalproducts.net/search/simple?query={requests.utils.quote(name)}",
                "source": "LOTUS (naturalproducts.net, CC0)"}
    except Exception:
        return None


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    plants = PLANTS[:limit] if limit else PLANTS
    data = {}
    if os.path.exists(OUT):
        data = json.load(open(OUT, encoding="utf-8"))
    print(f"Scrapeando {len(plants)} plantas en LOTUS (CC0)…")
    done = 0
    for p in plants:
        if p in data and data[p].get("compound_count"):
            done += 1; continue
        rec = fetch_plant(p)
        if rec:
            data[p] = rec
        done += 1
        time.sleep(0.6)  # cortesía con LOTUS
        if done % 15 == 0:
            tot = sum(v.get("compound_count", 0) for v in data.values())
            print(f"  {done}/{len(plants)} plantas · {tot} pares planta-compuesto")
            json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    tot = sum(v.get("compound_count", 0) for v in data.values())
    print(f"OK: {len(data)} plantas · {tot} pares planta-compuesto -> {OUT}")


if __name__ == "__main__":
    main()
