## Massive PDF filler (for IAE tax cancellation)

This script fills pdfs with tabular data from a csv file.
Quick and dirt implementation for the **cancelation forms
for the IAE tax**, commited here with two purposes:

- Further occassions we had to fill the same forms
- Serve as a starting point for a general tool to fill pdfs

## Installation

```bash
sudo apt install pdftk
pip install -r requirements
```


## General Usage

Given a form to fill (ie `input.pdf`) run:

```
pdftk input.pdf dump_data_fields
```

Then create a csv file having as column header the `FieldName`
And the data you want to fill for each pdf in the following rows.
You can define one of such fields are the base for the output pdf filename.

## IAE tax cancellation usage

Obtain 016 and 703 form models and save them as 016.pdf and 703.pdf.

TODO: Url for the pdf models

TODO: How to generate the csv from erp data




