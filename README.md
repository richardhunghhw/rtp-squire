# RTP Squire

## Setup 

Setup Google API, [official docs](https://developers.google.com/sheets/api/quickstart/python). Adding the `credentials.json` file into the root directory. 

Setup `.env` file from `.env.template`.

## Useful Commands

Testing 

```bash
python3 -m pytest tests/test_notion_journal.py -k test_create_orders_table_block
```