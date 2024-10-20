import json
import os
import sys
import uuid

from azure.core.exceptions import AzureError
from azure.cosmos import CosmosClient, PartitionKey

