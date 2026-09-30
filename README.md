# Iraq Geography Data

Structured, trilingual data on the governorates, districts, and subdistricts of Iraq — with names in English, Kurdish (Sorani), and Arabic. Designed for research, mapping, education, and software applications.

**Current coverage: 19 governorates · 175 districts · 540 subdistricts.**

## Features
- Complete governorate → district (`qada'a`) → subdistrict (`nahiya`) hierarchy for all of Iraq
- Trilingual names: English, Kurdish (Sorani), Arabic
- `notes` on disputed territories (e.g. Makhmur, Sinjar, Shekhan, Khanaqin/Kifri), recent district upgrades, and source conflicts
- `altNames` preserving variant spellings and former names (e.g. `Dubz` → Dibis)
- Cleaned, deduplicated, and reproducible — the whole build pipeline is in `data/`

## 🙌 We Appreciate Your Contribution!
We warmly welcome and appreciate your contributions to this project. Whether you have corrections, new data, translations, or code improvements, your input helps make this resource more complete and accurate. By contributing, you help researchers, developers, and educators across the world. **Join us in building a better open data resource for Iraq!**

## Usage
- The main data file is `data/output.json`, containing all governorates and their subdivisions.
- You can use this data in your applications, research, or for educational purposes.
- To rebuild `output.json` from the research files: `python3 data/merge_research.py && python3 data/dedup.py` (run from the repo root). The committed `output.json` is minified to keep the file small; pretty-print it locally with `python3 -m json.tool data/output.json` if you want a readable copy.

## Data Sources
- English Wikipedia — governorate/district articles, "Districts of Iraq"
- Arabic Wikipedia — governorate/district articles, قائمة نواحي العراق (list of Iraq's subdistricts)
- Kurdish (Sorani) Wikipedia — Kurdistan Region names
- [citypopulation.de](https://www.citypopulation.de/en/iraq/) — district/subdistrict population tables built on Iraq's Central Statistical Organization (COSIT) data and the 2024 census
- Kurdistan Region Statistics Office (KRSO) publications
- Iraqi Ministry of Planning approvals and governorate websites (for post-2014 nahiya → district upgrades)
- Community contributions and open data initiatives

If you use this data, please consider citing these sources and this repository.

## Data Structure
The data is organized as a JSON object with a top-level `provinces` array. Each province contains:
- `engName`: Governorate name in English
- `krdName`: Governorate name in Kurdish (Sorani)
- `arbName`: Governorate name in Arabic
- `notes` (optional): provenance notes, e.g. recent administrative changes
- `districts`: Array of districts, each with:
  - `engName`, `krdName`, `arbName`: District names
  - `altNames` (optional): variant spellings / former names
  - `notes` (optional): e.g. disputed-territory status, upgrade history
  - `subdistricts`: Array of subdistricts, each with:
    - `engName`, `krdName`, `arbName`: Subdistrict names
    - `notes` / `altNames` (optional)

## Coverage & Caveats
- **Recent upgrades:** between 2014–2026 many subdistricts were elevated to districts (especially in Basra, Thi Qar, Muthanna, Qadisiyyah, Wasit, Anbar, and Saladin). English Wikipedia still shows the older structure in places; this dataset follows the newer official structure and notes the conflicts.
- **Disputed territories** (Article 140 areas) appear under their federal (Baghdad-administered) governorate with a `notes` flag where the KRG claims them too — e.g. Makhmur, Shekhan, Akre, Khanaqin, Kifri.
- **Baghdad** carries both systems: the 10 official `qada'a` districts and the older Amanat Baghdad municipal districts, the latter marked in `notes`.
- **Villages** are not yet covered — contributions welcome (see below).

## How to Contribute
Contributions are welcome! If you have corrections, additional data (villages especially!), or improvements, please submit a pull request or open an issue. Raw research can go in `research/` following the existing JSON schema; then rebuild with the scripts in `data/`.

## Acknowledgements
Special thanks to everyone who contributed to this project, including those who provided data, translations, and code improvements. Your efforts help make this resource more accurate and useful for all.

**Thank you for your contributions!**
