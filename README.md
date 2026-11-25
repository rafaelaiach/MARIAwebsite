# Site de Maria Aiach, architecte DPLG

Nouveau site, reconstruit à partir du site Wix (mariaaiach.wixsite.com/monsite) :
mêmes textes, mêmes photos, les photos trop sombres éclaircies de façon naturelle.

## Le voir

Dans un terminal ouvert dans ce dossier :

```
cd site
python -m http.server 8090
```

Puis ouvrir http://127.0.0.1:8090 dans Chrome.

## Ce qu'il y a dedans

| Dossier / fichier | Rôle |
|---|---|
| `site/` | Le site fini, à mettre en ligne tel quel (pages HTML, photos, style) |
| `tools/build.py` | Fabrique toutes les pages. Les projets, leurs textes courts et les photos de couverture sont en haut du fichier |
| `tools/images.py` | Télécharge les photos depuis Wix et éclaircit celles qui sont trop sombres |
| `data/` | Textes et listes de photos lus sur l'ancien site |
| `cache/` | Photos d'origine (pas besoin de les mettre en ligne) |

Après un changement dans `tools/build.py` : `python tools/build.py`.

## Avant la mise en ligne

1. Choisir un nom de domaine (par exemple maria-aiach-architecte.fr) et le mettre dans `DOMAIN`, en haut de `tools/build.py`, puis relancer la fabrication.
2. Héberger le dossier `site/` : Netlify, Vercel, Cloudflare Pages ou GitHub Pages le font gratuitement.
3. Compléter l'hébergeur dans la page Mentions légales.
4. Déclarer le site dans Google Search Console et y envoyer `sitemap.xml`.
5. Créer une fiche Google Business Profile « Maria Aiach, architecte » : c'est elle qui fait apparaître le nom dans Google Maps et en haut des résultats.
