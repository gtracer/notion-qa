"""This is the logic for ingesting Notion data into LangChain."""
from pathlib import Path
from langchain.text_splitter import CharacterTextSplitter
import faiss
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
import pickle
import json
from types import SimpleNamespace


# # Here we load in the data in the format that Notion exports it in.
# ps = list(Path("Notion_DB/").glob("**/*.md"))

# data = []
# sources = []
# for p in ps:
#     with open(p) as f:
#         data.append(f.read())
#     sources.append(p)

import os
from notion_client import Client
from pprint import pprint

key = "secret_CnHybsrcQjqNZtGari6rxNdOLZt8DKw069uo9z47AoC"
notion = Client(auth=key)

# write a function to get all of the data from a notion database, including pagination if required

xs = "71dc1eeae27c4f16a3e6d2ea49c23ae1"
# list_users_response = notion.databases.retrieve(database_id=xs)
# pprint(list_users_response)

def get_all_notion_data():
    """Get all of the data from a notion database."""
    # get the first page of data
    response = notion.databases.query(
        database_id=xs,
    )
    # write code to deseralize the data from the response
    data = json.loads(response["results"])
    print("data" , data)


# data = '{"name": "John Smith", "hometown": {"name": "New York", "id": 123}}'

# Parse JSON into an object with attributes corresponding to dict keys.
    # x = json.loads(response, object_hook=lambda d: SimpleNamespace(**d))
    # print(type(x))

    # get the total number of pages
    total_pages = response["has_more"]

    # get the data from the first page
    data = response["results"]
    print("data" , data)
    print("------------------")

    # if there are more pages, then get the data from the rest of the pages
    if total_pages:
        # get the cursor for the next page
        next_cursor = response["next_cursor"]

        # loop through the rest of the pages
        while next_cursor:
            # get the next page of data
            response = notion.databases.query(
                database_id=xs,
                start_cursor=next_cursor,
                # filter={
                #     "property": "Status",
                #     "select": {
                #         "equals": "Done"
                #     }
                # },
                # sorts=[
                #     {
                #         "property": "Date",
                #         "direction": "ascending"
                #     }
                # ]
            )

            # get the data from the next page
            print("data" , response["results"])
            print("------------------")
            # data.extend(response["results"])

            # if there are more pages, then get the data from the rest of the pages
            if response["has_more"]:
                # get the cursor for the next page
                next_cursor = response["next_cursor"]
            else:
                # if there are no more pages, then set the cursor to None
                next_cursor = None

    return data


print(get_all_notion_data())

# # Here we split the documents, as needed, into smaller chunks.
# # We do this due to the context limits of the LLMs.
# text_splitter = CharacterTextSplitter(chunk_size=1500, separator="\n")
# docs = []
# metadatas = []
# for i, d in enumerate(data):
#     splits = text_splitter.split_text(d)
#     docs.extend(splits)
#     metadatas.extend([{"source": sources[i]}] * len(splits))


# print(docs)
# # return

# # Here we create a vector store from the documents and save it to disk.
# store = FAISS.from_texts(docs, OpenAIEmbeddings(), metadatas=metadatas)
# faiss.write_index(store.index, "docs.index")
# store.index = None
# with open("faiss_store.pkl", "wb") as f:
#     pickle.dump(store, f)
