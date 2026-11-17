# Sheng-Kai Hsu — personal website

Hugo site deployed to GitHub Pages by `.github/workflows/hugo.yaml`.

- **CV content** (positions, publications, preprints, talks) comes from
  [ShengKaiHsu/cv](https://github.com/ShengKaiHsu/cv). `scripts/sync_cv.py`
  converts its `cv.md` into `data/cv.json`. The deploy workflow runs it on every
  build and once a day, so CV updates reach the site automatically.
- **Bio, research interests, news, links and photo** are edited in `hugo.toml` under `[params]`.
- **Photo:** add a square `static/images/profile.jpg` and set `photo = 'images/profile.jpg'`.

Local preview:

```bash
python3 scripts/sync_cv.py
hugo server
```
