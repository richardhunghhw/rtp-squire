from notion_client import Client

from src.logger_config import setup_logger

logger = setup_logger(__name__)

class NotionJournal:
    NP_TAGS = "RTPS-Actions"
    NP_ORDERS_TABLE_ID = "RTPS-OrdersTable-Id"
    NP_ORDER_REFERENCES = "Order References"
    
    def __init__(self, token, database_id):
        """
        Initialize the notion API class
        """
        if (token is None):
            raise ValueError("Token is required")
        if (database_id is None):
            raise ValueError("Database ID is required")
        
        self.CLIENT=Client(auth=token)
        self.DATABASE_ID=database_id

    def query_db_for_refresh_orders(self):
        logger.info("Querying the database for any entries with tag 'refresh-orders'...")
        
        entries = self.CLIENT.databases.query(
            **{
                "database_id": self.DATABASE_ID,
                "filter": {
                    "property": self.NP_TAGS,
                    "multi_select": {
                        "contains": "refresh-orders"
                    }
                }
            }
        )
        logger.info("Successfully queried the database for [" + str(len(entries['results'])) + "] entries")
        
        # Extract id and order references from the results
        res = []
        for entry in entries['results']:
            order_references = entry["properties"][self.NP_ORDER_REFERENCES]["rich_text"]
            table_block_id = entry["properties"][self.NP_ORDERS_TABLE_ID]["rich_text"]
            if not table_block_id:
                table_block_id = [{"plain_text": None}]
            
            if order_references:
                res.append({
                    "id": entry["id"],
                    "order-references": order_references[0]["plain_text"].split(","),
                    "table-block-id": table_block_id[0]["plain_text"],
                    "action-tags": entry["properties"][self.NP_TAGS]["multi_select"]
                })
            else:
                logger.warning("Empty order references for entry [" + entry["id"] + "]")
                        
        return res
    
    def generate_orders_table_block_children(self, orders):
        table_rows = []

        # Create the data rows
        for order in orders: 
            table_rows.append({
                "type": "table_row",
                "table_row": {
                    "cells": [
                        [
                            {
                            "type": "text",
                            "text": {
                                "content": order[0],
                            },
                            }
                        ],
                        [
                            {
                            "type": "text",
                            "text": {
                                "content": order[1],
                            },
                            }
                        ],
                        [
                            {
                            "type": "text",
                            "text": {
                                "content": order[2],
                            },
                            }
                        ],
                        [
                            {
                            "type": "text",
                            "text": {
                                "content": order[3],
                            },
                            }
                        ],
                        [
                            {
                            "type": "text",
                            "text": {
                                "content": order[4],
                            },
                            }
                        ],
                        [
                            {
                            "type": "text",
                            "text": {
                                "content": order[5],
                            },
                            }
                        ],
                        [
                            {
                            "type": "text",
                            "text": {
                                "content": order[6],
                            },
                            }
                        ],
                        [
                            {
                            "type": "text",
                            "text": {
                                "content": order[7],
                            },
                            }
                        ],
                        [
                            {
                            "type": "text",
                            "text": {
                                "content": order[8],
                            },
                            }
                        ],
                        [
                            {
                            "type": "text",
                            "text": {
                                "content": order[9],
                            },
                            }
                        ],
                        [
                            {
                            "type": "text",
                            "text": {
                                "content": order[10],
                            },
                            }
                        ],
                        [
                            {
                            "type": "text",
                            "text": {
                                "content": order[11],
                            },
                            }
                        ],
                        [
                            {
                            "type": "text",
                            "text": {
                                "content": order[12],
                            },
                            }
                        ]
                    ]
                }
            })

        return table_rows
    
    def create_orders_table_block(self, parent_id, orders):
        logger.info("Creating a table block under parent id [" + parent_id + "]...")
        
        if (parent_id is None):
            raise ValueError("Parent ID is required")
        if (orders is None):
            raise ValueError("Orders are required")

        table_rows = self.generate_orders_table_block_children(orders)
        
        # Create the table block
        res = self.CLIENT.blocks.children.append(
            **{
                "block_id": parent_id,
                "children": [
                    {
                        "object": "block",
                        "type": "table",
                        "table": {
                            "table_width": 13,
                            "has_column_header": True,
                            "has_row_header": False,
                            "children": table_rows,
                        }
                    }
                ]
            }
        )
        
        logger.info("Successfully created table block with id [" + res["results"][0]["id"] + "] under parent id [" + parent_id + "]")
        return res["results"][0]["id"]

    def delete_block(self, block_id):
        logger.info("Deleting block with id [" + block_id + "]...")
        
        if (block_id is None):
            raise ValueError("Block ID is required")
        
        res = self.CLIENT.blocks.delete(
            **{
                "block_id": block_id
            }
        )
        
        logger.info("Successfully deleted block with id [" + block_id + "]")
        return res
    
    def update_entry_table_block_id(self, entry_id, table_block_id):
        if (entry_id is None):
            raise ValueError("Entry ID is required")
        if (table_block_id is None):
            raise ValueError("Table block ID is required")
        logger.info("Updating entry [" + entry_id + "] with table block id [" + table_block_id + "]...")  

        res = self.CLIENT.pages.update(
            **{
                "page_id": entry_id,
                "properties": {
                    self.NP_ORDERS_TABLE_ID: {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": table_block_id
                                }
                            }
                        ]
                    }
                }
            }
        )
        
        logger.info("Successfully updated entry [" + entry_id + "] with table block id [" + table_block_id + "]")
        return res
    
    def remove_refresh_orders_tag(self, entry_id, exisiting_tags=[]):
        if (entry_id is None):
            raise ValueError("Entry ID is required")
        
        tags = [tag for tag in exisiting_tags if tag["name"] != "refresh-orders"]
        
        res = self.CLIENT.pages.update(
            **{
                "page_id": entry_id,
                "properties": {
                    self.NP_TAGS: {
                        "multi_select": tags
                    }
                }
            }
        )
        
        return res
        