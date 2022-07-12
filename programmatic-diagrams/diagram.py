#!/usr/bin/env python3

from diagrams import Cluster, Diagram, Edge
from diagrams.custom import Custom
from diagrams.onprem import ci, cd
from diagrams.onprem.compute import Server
from diagrams.oci.compute import Functions, OCIRegistry, OKE
from diagrams.generic.device import Tablet
from diagrams.k8s.infra import Node as K8sNode
from diagrams.k8s.infra import Master as K8sControl
from diagrams.k8s.group import Namespace
from diagrams.k8s.compute import Pod, DaemonSet
from diagrams.onprem.vcs import Git

def QuayRegistry(text=""):
    return Custom(text, "./Logo-Red_Hat-Quay.io-A-Standard-RGB.png")

def OCPCluster(text=""):
    return Custom(text, "./Logo-Red_Hat-OpenShift_4-A-Standard-RGB.png")

def Laptop(text=""):
    return Custom(text, "./Icon-Red_Hat-Hardware-Laptop-B-Black-RGB.png")

with Diagram("Out Of Cluster Build Flow", show=False):
    user_action = Laptop("User Action") >> Edge(label="$ git push") >> Git("Git")
    quay = QuayRegistry()

    with Cluster("CI System"):
        build = user_action >> Edge(label="HTTP Event") >> [ci.Jenkins(), cd.Tekton()]
        build >> Edge(label="Image Push") >> quay

    dev_cluster = OCPCluster("dev")

    quay >> Edge(label="Image Pull") << dev_cluster
    build >> dev_cluster

    rollout = Laptop("$ oc apply -f new-image.yaml") >> Custom("staging", "./Logo-Red_Hat-OpenShift_4-A-Standard-RGB.png")

with Diagram("Final Image Build Flow", show=False):
    user_object_creation = Laptop("$ oc apply -f newosimage.yaml")
    user_object_query = Laptop("$ oc get newosimage")
    user_object_rollout = Laptop("$ oc rollout mcp/worker")
    with Cluster("OpenShift Cluster"):
        incluster_registry = OCIRegistry("In-Cluster Registry")
        with Cluster("Worker MCP"):
            worker_nodes = [K8sNode("worker_%s" % i) for i in range(0,3)]
        with Cluster("MCO") as mco_namespace:
            mcd_pod = DaemonSet("MCD")
            mcc_pod = Pod("MCC")
            preflight_checks = Pod("Preflight Checks")
            final_image_build = Pod("Final Image Build")

            user_object_creation >> mcc_pod
            mcc_pod >> Edge(label="Success / Fail") << preflight_checks
            mcc_pod >> Edge(label="Success / Fail") << final_image_build

            final_image_build >> Edge(label="Image Push") >> incluster_registry

            user_object_query >> Edge(label="Success / Fail") << mcc_pod

            user_object_rollout >> mcc_pod >> mcd_pod

            for worker_node in worker_nodes:
                mcd_pod >> Edge(label="$ rpm-ostree rebase") >> worker_node
                worker_node << Edge(label="Image Pull") << incluster_registry
