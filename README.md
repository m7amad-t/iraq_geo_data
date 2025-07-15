# Iraq Geography Data

This project provides detailed, structured data on the provinces, districts, subdistricts, and villages of Iraq, with names in English, Kurdish, and Arabic. The data is designed for use in research, mapping, educational, and software applications.

## Features
- Comprehensive list of Iraq's provinces, districts, and subdistricts
- Multilingual support: English, Kurdish, and Arabic names
- Cleaned and deduplicated data, ready for use

## 🙌 We Appreciate Your Contribution!
We warmly welcome and appreciate your contributions to this project. Whether you have corrections, new data, translations, or code improvements, your input helps make this resource more complete and accurate. By contributing, you help researchers, developers, and educators across the world. **Join us in building a better open data resource for Iraq!**

## Usage
- The main data file is `output.json`, containing all provinces and their subdivisions.
- You can use this data in your applications, research, or for educational purposes.
- If you wish to update or merge new data, scripts are provided (see `merge_json.py` and `fill_kurname.py`).

## Data Sources
- Wikipedia (Governorates, Districts, and Subdistricts of Iraq)
- Official Iraqi government publications
- Community contributions and open data initiatives

If you use this data, please consider citing these sources and this repository.

## Data Structure
The data is organized as a JSON object with a top-level `provinces` array. Each province contains:
- `engName`: Province name in English
- `kurName`: Province name in Kurdish
- `arbName`: Province name in Arabic
- `districts`: Array of districts, each with:
  - `engName`, `kurName`, `arbName`: District names
  - `subdistricts`: Array of subdistricts, each with:
    - `engName`, `kurName`, `arbName`: Subdistrict names
    - `villages`: Array of villages (if available), each with:
      - `engName`, `kurName`, `arbName`: Village names

Some provinces may also have a `subdistricts` array at the province level, depending on the data source.

## How to Contribute
Contributions are welcome! If you have corrections, additional data, or improvements, please submit a pull request or open an issue.

## Acknowledgements
Special thanks to everyone who contributed to this project, including those who provided data, translations, and code improvements. Your efforts help make this resource more accurate and useful for all.

**Thank you for your contributions!** 