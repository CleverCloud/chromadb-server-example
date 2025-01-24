# Deploy ChromaDB as a persistent server on Clever Cloud

To follow this tutorial, you need a [Clever Cloud account](https://console.clever-cloud.com) and [Clever Tools](https://github.com/CleverCloud/clever-tools):

```bash
npm i -g clever-tools
clever login
```

## Create resources

Create a Python application with a FS Bucket:

```bash
git clone https://github.com/CleverCloud/chromadb-server-example
cd chromadb-server-example

clever create -t python
clever addon create fs-bucket chromaFS
```

After FS Bucket deployment, you'll get:

```bash
Add-on created successfully!
ID: addon_xxx
Real ID: bucket_yyy
```

Keep the `yyy` part for the next step.

## Configure ChromaDB Server with auth

```bash
# Add the FS Bucket host to your application, link it to the `/db` folder
# Replace 'yyy' with the real ID part from the previous step
clever env set CC_FS_BUCKET "/db:bucket-yyy-fsbucket.services.clever-cloud.com"

# Generate a login:password pair, configure it for ChromaDB and add it to your application
# Replace 'admin' with your login and 'password' with your password
clever env set CHROMA_SERVER_AUTHN_PROVIDER "chromadb.auth.basic_authn.BasicAuthenticationServerProvider"
clever env set CHROMA_SERVER_AUTHN_CREDENTIALS $(htpasswd -Bbn admin password)

# Configure the ChromaDB server launch
clever env set CC_RUN_COMMAND "chroma run --host 0.0.0.0 --port 9000 --path db/data"
```

## Deploy the application

```bash
clever deploy
```

## Test script

Once the server is deployed, you can test it with the following Python script:

```python
import os
import chromadb

from dotenv import load_dotenv
from datetime import datetime
from chromadb.config import Settings

load_dotenv()

chroma_client = chromadb.HttpClient(
    # Replace 'app-xxx.cleverapps.io' with your application host
    # You can get the domain of your application with `clever domain` command
    host="app-xxx.cleverapps.io",
    port=80,
    settings=Settings(
        chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
        chroma_client_auth_credentials=os.getenv("CHROMA_CLIENT_AUTH_CREDENTIALS")
    )
)

collection = chroma_client.create_collection(name="my_collection")

collection.add(
    documents=[
        "This is a document about pineapple",
        "This is a document about oranges"
    ],
    ids=["id1", "id2"]
)

results = collection.query(
    query_texts=["This is a query document about hawaii"],
    n_results=2
)

print(results)

# Uncomment to delete the collection after printing the results
# chroma_client.delete_collection(name="my_collection")
```

You'll need to `export CHROMA_CLIENT_AUTH_CREDENTIALS="admin:password"` with your corresponding login and password before running the script.
