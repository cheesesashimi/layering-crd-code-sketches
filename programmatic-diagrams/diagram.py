#!/usr/bin/env python3

from diagrams import Cluster, Diagram, Edge, Node
from diagrams.custom import Custom
from diagrams.onprem import ci, cd
from diagrams.onprem.compute import Server
from diagrams.oci.compute import Container, Functions, OCIRegistry, OKE
from diagrams.generic.device import Tablet
from diagrams.k8s.infra import Node as K8sNode
from diagrams.k8s.infra import Master as K8sControl
from diagrams.k8s.group import Namespace
from diagrams.k8s.compute import Pod, DaemonSet
from diagrams.onprem.vcs import Git

def ARM64(text=""):
    return Custom(text, "./Arm-logo-blue-pms313.svg")

def AMD64(text=""):
    return Custom(text, "./amd64_logo.svg")

def POWER(text=""):
    return Node("POWER " + text)

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

with Diagram("Multiarch Scenario 1", show=False):
    with Cluster("OpenShift Cluster"):
        base_image_manifest_list = Node("Base Image Manifest List")
        amd64_manifest = AMD64("AMD 64 Manifest")
        master_mcp = Container("master\nMCP / Layered Image")
        worker_mcp = Container("worker\nMCP / Layered Image")
        amd64_control_plane = K8sControl("AMD64")
        amd64_workers = K8sNode("AMD64 Workers\n(worker)")

        base_image_manifest_list >> amd64_manifest >> [master_mcp, worker_mcp]
        master_mcp >> amd64_control_plane
        worker_mcp >> amd64_workers

with Diagram("Multiarch Scenario 2", show=False):
    with Cluster("OpenShift Cluster"):
        base_image_manifest_list = Node("Base Image Manifest List")
        amd64_manifest = AMD64("AMD 64 Manifest")
        arm64_manifest = ARM64("ARM 64 Manifest")
        master_mcp = Container("master\nMCP / Layered Image")
        worker_mcp = Container("worker\nMCP / Layered Image")
        amd64_control_plane = K8sControl("AMD64")
        arm64_workers = K8sNode("ARM64 Workers\n(worker)")

        base_image_manifest_list >> amd64_manifest >> master_mcp >> amd64_control_plane
        base_image_manifest_list >> arm64_manifest >> worker_mcp >> arm64_workers

with Diagram("Multiarch Scenario 3", show=False):
    with Cluster("OpenShift Cluster"):
        base_image_manifest_list = Node("Base Image Manifest List")
        amd64_manifest = AMD64("AMD 64 Manifest")
        arm64_manifest = ARM64("ARM 64 Manifest")
        master_mcp = Container("Master MCP / Layered Image")
        arm64_worker_mcp = Container("worker-arm64\nWorker MCP / Layered Image")
        amd64_worker_mcp = Container("worker-amd64\nWorker MCP / Layered Image")
        amd64_control_plane = K8sControl("AMD64")
        arm64_workers = K8sNode("ARM64 Workers\n(worker-arm64)")
        amd64_workers = K8sNode("AMD64 Workers\n(worker-amd64)")

        base_image_manifest_list >> amd64_manifest >> master_mcp >> amd64_control_plane
        amd64_manifest >> amd64_worker_mcp >> amd64_workers
        base_image_manifest_list >> arm64_manifest >> arm64_worker_mcp >> arm64_workers

with Diagram("Multiarch Scenario 4", show=False):
    with Cluster("OpenShift Cluster"):
        base_image_manifest_list = Node("Base Image Manifest List")
        amd64_manifest = AMD64("AMD 64 Manifest")
        power_manifest = POWER("POWER Manifest")
        master_mcp = Container("Master MCP / Layered Image")
        streaming_worker_mcp = Container("worker-power-streaming\nWorker MCP / Layered Image")
        transactional_worker_mcp = Container("worker-power-transactional\nWorker MCP / Layered Image")
        amd64_control_plane = K8sControl("AMD64")
        streaming_workers = K8sNode("POWER Workers\n(worker-power-streaming)")
        transactional_workers = K8sNode("AMD64 Workers\n(worker-power-transactional)")

        base_image_manifest_list >> amd64_manifest >> master_mcp >> amd64_control_plane
        base_image_manifest_list >> power_manifest >> [streaming_worker_mcp, transactional_worker_mcp]
        streaming_worker_mcp >> streaming_workers
        transactional_worker_mcp >> transactional_workers
