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
├── requirements.txt         # Python dependencies (chromadb)
└── README.md                # This documentation
```

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

```bash
# Step 6: Add the FS Bucket host to your application, link it to the `/db` folder
# Replace 'yyy' with the real ID part from the previous step
clever env set CC_FS_BUCKET "/db:bucket-yyy-fsbucket.services.clever-cloud.com"

# Step 7: Generate a login:password pair, configure it for ChromaDB
# Replace '<USERNAME>' with your login and '<PASSWORD>' with your password
clever env set CHROMA_SERVER_AUTHN_PROVIDER "chromadb.auth.basic_authn.BasicAuthenticationServerProvider"
clever env set CHROMA_SERVER_AUTHN_CREDENTIALS $(htpasswd -Bbn <USERNAME> <PASSWORD>)

# Step 8: Configure the ChromaDB server launch
clever env set CC_RUN_COMMAND "chroma run --host 0.0.0.0 --port 9000 --path db/data"

# Step 9: Deploy your application
clever deploy
```

## Accessing Your ChromaDB Server

Once deployed, your ChromaDB server will be available at:
- https://<YOUR_DOMAIN_NAME> (if you configured a custom domain)
- https://app-xxx.cleverapps.io (Clever Cloud generated domain)

You can get your application's domain with:

```bash
clever domain
```

## Using Your ChromaDB Server

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
    port=80,
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
| `CHROMA_SERVER_AUTHN_PROVIDER` | Authentication provider for ChromaDB |
| `CHROMA_SERVER_AUTHN_CREDENTIALS` | Encoded credentials for ChromaDB authentication |
| `CC_RUN_COMMAND` | Command to start the ChromaDB server |

## Customizing Your Application

### Changing ChromaDB Version

To use a specific version of ChromaDB, update the `requirements.txt` file:

```
chromadb==0.4.18  # Replace with your desired version
```

### Additional Configuration

ChromaDB supports various configuration options. You can add them to your `CC_RUN_COMMAND` environment variable:

```bash
clever env set CC_RUN_COMMAND "chroma run --host 0.0.0.0 --port 9000 --path db/data --telemetry-enabled false"
```

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
