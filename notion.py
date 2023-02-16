
from notion_client import APIResponseError
import notion_client
import json
import logging


# key = "secret_CnHybsrcQjqNZtGari6rxNdOLZt8DKw069uo9z47AoC"
key2 = "secret_v2yIelamqWeGhhU7h2yRoZNW3vo5PEAL665Aknp7iZG"
notion = notion_client.Client(auth=key2)

# extract content from block based on type 
parsed_ids = {}
result = []

def extract_text(rich_text):
    content = ""
    for entry in rich_text:
        content += entry['plain_text']
        if entry['href'] is not None:
            content += " url (" + entry['href'] + ")"


    return content

def extract_block_info(block):
    content = None
    if block['type'] == 'paragraph':
        if block['paragraph']['rich_text']:
            content = extract_text(block['paragraph']['rich_text'])
    elif block['type'] == 'heading_1':
        if block['heading_1']['rich_text']:
            content = extract_text(block['heading_1']['rich_text'])
    elif block['type'] == 'heading_2':
        if block['heading_2']['rich_text']:
            content = extract_text(block['heading_2']['rich_text'])
    elif block['type'] == 'heading_3':
        if block['heading_3']['rich_text']:
            content = extract_text(block['heading_3']['rich_text'])
    elif block['type'] == 'bulleted_list_item':
        if block['bulleted_list_item']['rich_text']:
            content = extract_text(block['bulleted_list_item']['rich_text'])
    elif block['type'] == 'numbered_list_item':
        if block['numbered_list_item']['rich_text']:
            content = extract_text(block['numbered_list_item']['rich_text'])
    elif block['type'] == 'to_do':
        if block['to_do']['rich_text']:
            content = extract_text(block['to_do']['rich_text'])
    elif block['type'] == 'toggle':
        if block['toggle']['rich_text']:
            content = extract_text(block['toggle']['rich_text'])
    elif block['type'] == 'quote':
        if block['quote']['rich_text']:
            content = extract_text(block['quote']['rich_text'])
    elif block['type'] == 'code':
        if block['code']['title']:
            content = block['code']['title'][0]['plain_text']
    elif block['type'] == 'embed':
        if block['embed']['caption']:
            content = block['embed']['caption'][0]['plain_text']
    elif block['type'] == 'image':
        if block['image']['caption']:
            content = block['image']['caption'][0]['plain_text']
    elif block['type'] == 'video':
        if block['video']['caption']:
            content = block['video']['caption'][0]['plain_text']
    elif block['type'] == 'child_page':
        if block['child_page']['title']:
            content = block['child_page']['title']
    else:
        print(block['type'])
        content = None
    
    return content

def block_parser(block: dict, notion: "notion_client.client.Client")-> dict:
    #if the block will already be parsed later on then we only want to add the title here
    content = extract_block_info(block)
    if block["type"] in ['page', 'child_page', 'child_database']:
        return content
        
    if block["has_children"]:
        block["children"] = []
        start_cursor = None
        while True:
            if start_cursor is None:
                blocks = notion.blocks.children.list(block["id"])
            start_cursor = blocks["next_cursor"]
            block["children"].extend(blocks['results'])
            if start_cursor is None:
                break  
        
        for child_block in block["children"]:
            c = block_parser(child_block, notion)
            if c is None:
                continue
            content += " " + c
    return content

def notion_page_parser(page_id: str, notion: "notion_client.client.Client"):
    try:
        page = notion.pages.retrieve(page_id)
        page_type = 'page'

    except APIResponseError:
        print("error occured fetching page")
        pass
    
    start_cursor = None

    all_blocks = []
    while True:
        if start_cursor is None:
            blocks = notion.blocks.children.list(page_id)
        else:
            blocks = notion.blocks.children.list(page_id, start_cursor=start_cursor)
        start_cursor = blocks['next_cursor']
        all_blocks.extend(blocks['results'])
        if start_cursor is None:
            break  
    
    content = page['properties']['title']['title'][0]['plain_text']
    for block in all_blocks:
        block_content = block_parser(block, notion)
        if block_content is None:
            continue
        content += " " + block_content
    result.append(content)

class RowProperty:
    def __init__(self, key, property):
        self.name = key
        self.value = ""
        self.type = property['type']
        if property['type'] == 'select':
            if property['select'] and 'name' in property['select']:
                self.value = property['select']['name']
        elif property['type'] == 'multi_select':
            self.value = [x['name'] for x in property['multi_select']].join(', ')
        elif property['type'] == 'title':
            # self.value = property['title'][0]['plain_text']
            self.value = ''.join([x['plain_text'] for x in property['title']])
        elif property['type'] == 'rich_text':
            # self.value = property['rich_text'][0]['plain_text']
            self.value = ''.join([x['plain_text'] for x in property['rich_text']])
        elif property['type'] == 'number':
            self.value = property['number']
        elif property['type'] == 'date':
            if property['date'] and 'start' in property['date']:
                self.value = property['date']['start']
        elif property['type'] == 'people':
            self.value = ''.join([x['name'] for x in property['people']])
        elif property['type'] == 'files':
            self.value = ''.join([x['name'] for x in property['files']])
        elif property['type'] == 'checkbox':
            self.value = property['checkbox']  
        elif property['type'] == 'url':
            self.value = property['url']
        elif property['type'] == 'email':
            self.value = property['email']
        elif property['type'] == 'phone_number':
            self.value = property['phone_number']
        else:
            print("Unknown property type: ", property['type'], " for key: ", key, " and value: ", property)   

class NotionRow:
    def __init__(self, row):
        self.created_time = row["created_time"]
        self.last_edited_time = row["last_edited_time"]
        self.id = row["id"]
        self.properties = [RowProperty(key, value) for key, value in row["properties"].items()]
    
    def serialize(self, database_name):
        template = f'''
            Database:  {database_name}
            Created Time: {self.created_time}
            Last Edited Time: {self.last_edited_time}
        '''

        for prop in self.properties:
            template += f'column name: {prop.name} column value: {prop.value} column data type: {prop.type} | '
        
        return template


def get_rows(response):
    # get the results from the first page 
    extracted = []
    rows = response["results"]
    database_name = "Moonchaser: Candidates CRM"
    for row in rows:
        clean_row = NotionRow(row)
        extracted.append(clean_row.serialize(database_name))
        # create string that contains all of the properties

    return extracted


def get_db_data(database_id):
    """Get all of the data from a notion database."""
    # get the first page of data
    response = notion.databases.query(
        database_id=database_id,
    )

    # get the total number of pages
    total_pages = response["has_more"]

    rows = get_rows(response)
    # if there are more pages, then get the data from the rest of the pages
    if total_pages:
        # get the cursor for the next page
        next_cursor = response["next_cursor"]

        # loop through the rest of the pages
        while next_cursor:
            # get the next page of data
            response = notion.databases.query(
                database_id=database_id,
                start_cursor=next_cursor,
            )

            rows.append(get_rows(response))

            # if there are more pages, then get the data from the rest of the pages
            if response["has_more"]:
                # get the cursor for the next page
                next_cursor = response["next_cursor"]
            else:
                # if there are no more pages, then set the cursor to None
                next_cursor = None

    return rows


#Use notion search api endpoint to get all pages and databases
def get_all_pages_and_databases(notion):
    start_cursor = None
    while True:
        if start_cursor is None:
            res = notion.search()
        else:
            res = notion.search(start_cursor=start_cursor)
        
        for entity in res['results']:
            if entity['object'] == 'page':
                # I don't want to get all the pages in the database here
                if entity['parent']['type'] == 'database_id':
                    continue
                notion_page_parser(entity['id'], notion)
            elif entity['object'] == 'database':
                result.extend(get_db_data(entity['id']))
            #we don't care about users right now
        if res["has_more"] == False or res["next_cursor"] is None:
            break
        start_cursor = res["next_cursor"]
    # return embeddings

def create():
    get_all_pages_and_databases(notion)
    print(result)


create()

 
    
