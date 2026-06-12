![Clever Cloud logo](/github-assets/clever-cloud-logo.png)

# ChromaDB Server Example on Clever Cloud
[![Clever Cloud - PaaS](https://img.shields.io/badge/Clever%20Cloud-PaaS-orange)](https://clever-cloud.com)

## Overview

This repository provides a complete guide for deploying a ChromaDB vector database server on [Clever Cloud](https://clever-cloud.com), a European PaaS provider.

[ChromaDB](https://www.trychroma.com/) is an open-source embedding database designed for AI applications. It allows you to store and query embeddings and their associated metadata, making it ideal for semantic search, RAG (Retrieval Augmented Generation), and other AI applications that require efficient similarity search.

This example demonstrates how to deploy a persistent ChromaDB server with authentication on Clever Cloud, using a FS Bucket for data persistence.

## Prerequisites

- A [Clever Cloud account](https://console.clever-cloud.com)
- [Clever Tools CLI](https://github.com/CleverCloud/clever-tools) installed and configured
- Basic familiarity with command line operations
- Basic understanding of Python and [ChromaDB](https://docs.trychroma.com/)
- A domain name (optional, but recommended for production use)

## Project Structure

```
├── requirements.txt         # Python dependencies (chromadb + proxy stack)
├── proxy.py                 # Basic-auth reverse proxy that secures the server
└── README.md                # This documentation
```

> **Why a proxy?** ChromaDB 1.x removed native authentication — the `chroma run`
> server ignores the `CHROMA_SERVER_AUTHN_*` settings and listens with no access
> control. To keep this example secure, ChromaDB runs privately on localhost and
> a small reverse proxy (`proxy.py`) handles HTTP Basic authentication on the
> public port, forwarding only authorized requests. The client code is standard
> Chroma Basic auth, so nothing changes on the client side.

## Deployment Guide

### Before You Begin

Before starting the deployment process, you'll need to decide on:
- Application Name: Choose a unique name for your ChromaDB server (e.g., my-chromadb-server)
- Domain Name: Optionally, choose a domain name for your application
- Authentication Credentials: Username and password for securing your ChromaDB server

You'll use these values throughout the deployment process. In the commands below, replace:
- `<APP_NAME>` with your chosen application name
- `<YOUR_DOMAIN_NAME>` with your domain name (if applicable)
- `<USERNAME>` and `<PASSWORD>` with your chosen authentication credentials

### Using Clever Tools CLI

Follow these steps to deploy your ChromaDB server on Clever Cloud:

```bash
# Step 1: Clone this repository
git clone https://github.com/CleverCloud/chromadb-server-example
cd chromadb-server-example

# Step 2: Login to Clever Cloud if you haven't already
clever login

# Step 3: Create a Python application
clever create -t python <APP_NAME>

# Step 4: Add your domain (optional but recommended)
clever domain add <YOUR_DOMAIN_NAME>

# Step 5: Create a FS Bucket for data persistence
clever addon create fs-bucket chromaFS
```

After FS Bucket deployment, you'll get:

```bash
Add-on created successfully!
ID: addon_xxx
Real ID: bucket_yyy
```

Keep the `yyy` part for the next step.

### Configure ChromaDB Server with Authentication

The application runs two processes in the same Clever Cloud app:

- **ChromaDB** runs privately on `127.0.0.1:8000`, started as a [Clever Cloud worker](https://developers.clever-cloud.com/doc/develop/workers/).
- **`proxy.py`** runs on the public port `9000`, validates HTTP Basic credentials, and forwards authorized requests to ChromaDB. It is the application's run command.

```bash
# Step 6: Add the FS Bucket host to your application, link it to the `/db` folder
# Replace 'yyy' with the real ID part from the previous step
clever env set CC_FS_BUCKET "/db:bucket-yyy-fsbucket.services.clever-cloud.com"

# Step 7: Generate a login:password pair for the proxy to enforce
# Replace '<USERNAME>' with your login and '<PASSWORD>' with your password
clever env set PROXY_AUTH_CREDENTIALS "$(htpasswd -Bbn <USERNAME> <PASSWORD>)"

# Step 8: Run ChromaDB privately as a worker (localhost only, never exposed)
clever env set CC_WORKER_COMMAND_0 "chroma run --host 127.0.0.1 --port 8000 --path db/data"

# Step 9: Run the auth proxy on the public port as the application's run command
clever env set CC_RUN_COMMAND "python proxy.py"

# Step 10: Deploy your application
clever deploy
```

> **Note:** On Clever Cloud a Python app started via `CC_RUN_COMMAND` must listen
> on port `9000` — `proxy.py` does this by default. ChromaDB stays on its private
> `8000` port and is only reachable through the proxy.

## Accessing Your ChromaDB Server

Once deployed, your ChromaDB server will be available at:
- https://<YOUR_DOMAIN_NAME> (if you configured a custom domain)
- https://app-xxx.cleverapps.io (Clever Cloud generated domain)

You can get your application's domain with:

```bash
clever domain
```

## Using Your ChromaDB Server

The sample client below uses [`python-dotenv`](https://pypi.org/project/python-dotenv/) to optionally read credentials from a `.env` file. Install the two libraries it needs:

```bash
pip install chromadb python-dotenv
```

Here's a sample Python script to interact with your deployed ChromaDB server:

```python
import os
import chromadb
from dotenv import load_dotenv
from chromadb.config import Settings

# Load environment variables from .env file (optional)
load_dotenv()

# Connect to your ChromaDB server
chroma_client = chromadb.HttpClient(
    # Replace with your application host
    host="app-xxx.cleverapps.io",  # or your custom domain
    port=443,
    ssl=True,  # use HTTPS so Basic auth credentials are not sent in cleartext
    settings=Settings(
        chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
        chroma_client_auth_credentials=os.getenv("CHROMA_CLIENT_AUTH_CREDENTIALS")
    )
)

# Create a collection
collection = chroma_client.create_collection(name="my_collection")

# Add documents with embeddings
collection.add(
    documents=[
        "This is a document about pineapple",
        "This is a document about oranges"
    ],
    ids=["id1", "id2"]
)

# Query the collection
results = collection.query(
    query_texts=["This is a query document about hawaii"],
    n_results=2
)

print(results)

# Uncomment to delete the collection after printing the results
# chroma_client.delete_collection(name="my_collection")
```

Before running the script, set your authentication credentials:

```bash
export CHROMA_CLIENT_AUTH_CREDENTIALS="<USERNAME>:<PASSWORD>"
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `CC_FS_BUCKET` | Configuration for the FS Bucket mounted at `/db` |
| `PROXY_AUTH_CREDENTIALS` | `htpasswd`-style `user:hash` line the proxy validates Basic auth against |
| `CC_WORKER_COMMAND_0` | Command to start the private ChromaDB server (worker) |
| `CC_RUN_COMMAND` | Command to start the auth proxy on the public port (`python proxy.py`) |
| `CHROMA_UPSTREAM` | Optional. Upstream ChromaDB URL the proxy forwards to (default `http://127.0.0.1:8000`) |
| `ANONYMIZED_TELEMETRY` | Optional. Set to `False` to disable ChromaDB's anonymized telemetry |

## Customizing Your Application

### Changing ChromaDB Version

To use a specific version of ChromaDB, update the `requirements.txt` file:

```
chromadb==1.5.9  # Replace with your desired version
```

### Additional Configuration

ChromaDB supports various configuration options. You can tweak the server launch command in your `CC_WORKER_COMMAND_0` environment variable (keep it on the private `127.0.0.1:8000` address so it stays behind the proxy):

```bash
clever env set CC_WORKER_COMMAND_0 "chroma run --host 127.0.0.1 --port 8000 --path db/data"
```

To disable anonymized telemetry, set the dedicated environment variable (`chroma run` doesn't expose a telemetry flag; telemetry is controlled via the `ANONYMIZED_TELEMETRY` environment variable):

```bash
clever env set ANONYMIZED_TELEMETRY "False"
```

## Testing Locally

You can run the exact same setup on your machine before deploying:

```bash
# 1. Create a virtual environment and install the dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Start ChromaDB privately (in one terminal)
chroma run --host 127.0.0.1 --port 8000 --path db/data

# 3. Start the auth proxy on the public port (in another terminal)
export PROXY_AUTH_CREDENTIALS="$(htpasswd -Bbn myuser mypass)"
python proxy.py

# 4. Connect with the client (port 9000, no TLS locally)
export CHROMA_CLIENT_AUTH_CREDENTIALS="myuser:mypass"
# In the sample client, set host="localhost", port=9000, ssl=False
```

Requests with the wrong (or no) credentials are rejected with `401 Unauthorized`;
only `myuser:mypass` gets through to ChromaDB.

## Troubleshooting

### Viewing Logs

To view your application logs:

```bash
clever logs
```

### Common Issues

- **Connection Refused**: Ensure your client is using the correct host, port, and authentication credentials
- **Authentication Failed**: Verify your CHROMA_CLIENT_AUTH_CREDENTIALS environment variable matches the credentials set during deployment
- **Data Persistence Issues**: Check that the FS Bucket is properly mounted and accessible

## Resources

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Clever Cloud Documentation](https://www.clever-cloud.com/doc/)
- [FS Bucket Documentation](https://www.clever-cloud.com/doc/deploy/addon/fs-bucket/)
