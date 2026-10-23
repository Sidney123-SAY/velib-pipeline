# Pipeline de collecte Vélib'

Capture l'état des stations Vélib' d'Île-de-France toutes les 15 minutes, archive les
réponses brutes, puis les transforme en un jeu de données interrogeable en SQL.

**L'intérêt du projet tient en une phrase :** l'API Vélib' ne publie que l'instant présent.
Personne ne sait combien il y avait de vélos à une station donnée hier à 8 h cette
information est écrasée en continu. Ce pipeline fabrique un historique qui n'existe
nulle part ailleurs.

---

## Architecture

```
          API Vélib' Métropole
   station_information.json + station_status.json
                   |
                   |  ingest.py  ·  toutes les 15 min
                   v
          raw/<endpoint>/<AAAA-MM-JJ>/<HH-MM-SS>.json
          JSON brut horodaté · jamais modifié
                   |
                   |  transform.py
                   v
          staging/station_status/<AAAA-MM-JJ>.parquet
          staging/dim_station.parquet
          typé · aplati · dédoublonné
                   |
                   |  load.py
                   v
          warehouse.duckdb
          dim_station · fact_station_status · dim_temps
                   |
                   |  queries.sql
                   v
          Analyse : taux de remplissage, flux pendulaires
```

La couche `raw/` n'est jamais réécrite. Si une règle de nettoyage se révèle mauvaise,
il suffit de corriger `transform.py` et de rejouer tout l'historique collecté sans
rappeler l'API une seule fois.

---

## État d'avancement

- [x] Ingestion planifiée en production depuis le 16 octobre 2026
- [X] Transformation vers Parquet
- [X] Chargement en entrepôt DuckDB
- [X] Contrôles qualité
- [X] Requêtes d'analyse

---

## Les scripts

| Fichier | Rôle |
| --- | --- |
| `explore.py` | Premier contact avec l'API : compte les stations, affiche un enregistrement |
| `ingest.py` | Appelle les deux points d'entrée, archive le JSON brut horodaté |
| `run_ingest.bat` | Lanceur appelé par le Planificateur de tâches Windows |
| `transform.py` | *(en cours)* JSON brut → Parquet typé et nettoyé |
| `load.py` | *(en cours)* Parquet → entrepôt DuckDB, schéma en étoile |

---

## Relancer le projet de zéro

```powershell
git clone https://github.com/<Sidney123-SAY>/velib-pipeline.git
cd velib-pipeline
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python ingest.py
```

Pour automatiser la collecte toutes les 15 minutes :

```powershell
schtasks /Create /TN "Velib ingest" /TR "C:\Users\Sidney\Documents\velib-pipeline\run_ingest.bat" /SC MINUTE /MO 15 /ST 00:00 /F
```

Le fichier `run_ingest.bat` doit pointer vers le Python de l'environnement virtuel,
et non vers le Python global sinon les dépendances ne sont pas trouvées.

---

## Décisions de conception

**Aucune transformation à l'ingestion.** `ingest.py` écrit la réponse de l'API telle
quelle. C'est contre-intuitif quand on vient de l'analyse, où le réflexe est de nettoyer
tout de suite. Mais l'instant est passé : une donnée filtrée à tort est perdue
définitivement. En gardant le brut, n'importe quelle règle de nettoyage peut être
corrigée et rejouée.

**Horodatage en UTC, jamais en heure locale.** Le dernier dimanche d'octobre, la France
repasse à l'heure d'hiver et 3 h redevient 2 h. En heure locale, deux captures portent
alors le même nom de fichier et l'une écrase l'autre ; l'axe temporel contient une heure
en double. La conversion vers l'heure de Paris n'a lieu qu'au moment de l'analyse.

**Horodatage côté client, pas celui de l'API.** Le champ `lastUpdatedOther` est l'heure
du serveur et n'est pas toujours cohérente. Chaque fichier archivé porte son propre
`captured_at`, plus l'URL appelée : il est lisible et datable sans rien connaître de son
origine.

**Une capture toutes les 15 minutes.** L'API annonce un `ttl` d'une heure mais se
rafraîchit bien plus souvent. Quinze minutes suffisent à voir les variations des heures
de pointe sans produire un volume ingérable sur une machine personnelle.

**Réessais espacés en cas d'échec réseau.** Trois tentatives, avec une attente qui double
à chaque fois, puis échec franc. Une micro-coupure ne doit pas créer un trou permanent ;
une panne réelle doit s'arrêter bruyamment et apparaître dans le journal.

---

## Limites connues

- La collecte ne tourne que lorsque la machine est allumée. Les nuits produisent des
  trous, mesurés et documentés à l'étape des contrôles qualité plutôt que dissimulés.
- Sur certaines stations, la somme des vélos mécaniques et électriques ne correspond pas
  au total annoncé. Les compteurs d'une API temps réel se désynchronisent ; l'écart sera
  quantifié avant de décider quelle valeur fait foi.
- Les stations dont la dernière remontée date de plus de deux heures sont écartées à la
  transformation. Ce seuil est un choix, pas une vérité il reste à valider sur les
  données réellement collectées.

---

## Données

Source : données ouvertes Vélib' Métropole, au format GBFS, diffusées publiquement et
sans clé d'API. Les fichiers collectés ne sont pas versionnés dans ce dépôt : `raw/`,
`staging/` et `warehouse.duckdb` sont exclus par `.gitignore`. Un dépôt de code ne
contient pas de données.
