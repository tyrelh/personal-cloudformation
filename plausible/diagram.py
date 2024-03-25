#!/usr/local/bin/python3
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway, APIGatewayEndpoint
from diagrams.saas.chat import Slack
from diagrams.custom import Custom
from diagrams.aws.security import SecretsManager

# graphviz.org/doc/info/attrs.html
graph_attr = {
    "fontsize": "25",
    "pad": "0.3"
}

images_path = "../../diagram-resources/"

with Diagram("DevBot Service", graph_attr=graph_attr, show=False):
    with Cluster("AWS"):