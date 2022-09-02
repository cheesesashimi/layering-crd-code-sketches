#!/usr/bin/env python3

import inspect
import json
import os
import shutil
import subprocess
import sys


HYPERSHIFT_NAMESPACE = "hypershift"
ENTRYPOINT_SCRIPT_PATH = "in-cluster-entrypoint-script.sh"
IN_CLUSTER_SCRIPT_PATH = "in-cluster-update-script.py"
MANIFEST_PATH = "clusters-namespace-deployment.yaml"


def run_oc_json_cmd(args):
    cmd = subprocess.run(args, capture_output=True)
    cmd.check_returncode()
    return json.loads(cmd.stdout)


def load_manifests():
    # Shell out to yq to convert YAML to JSON since Python does not have a
    # built-in YAML parser.
    # $ yq eval-all -o=json '[.]' ./clusters-namespace-deployment.yaml
    return run_oc_json_cmd([
        shutil.which("yq"),
        "eval-all",
        "-o=json",
        "[.]",
        os.path.join(os.path.dirname(__file__), MANIFEST_PATH)
    ])


def load_release_info():
    return run_oc_json_cmd([
        shutil.which("oc"),
        "adm",
        "release",
        "info",
        "-o=json"
    ])


def get_cli_image_pullspec():
    # '.references.spec.tags'
    release_info = load_release_info()
    for tag in release_info["references"]["spec"]["tags"]:
        if tag["name"] == "cli":
            return tag["from"]["name"]


def inject_incluster_script(configmap):
    with open(os.path.join(os.path.dirname(__file__), IN_CLUSTER_SCRIPT_PATH), "r") as script_file:
        script = script_file.read()

    configmap["data"]["script.py"] = script
    return configmap


def load_entrypoint_script():
    with open(os.path.join(os.path.dirname(__file__), ENTRYPOINT_SCRIPT_PATH), "r") as script_file:
        return script_file.read()

    deployment["spec"]["template"]["spec"]["initContainers"][1]["command"][2] = script
    return deployment


def prepare_deployment(deployment):
    #deployment["spec"]["template"]["spec"]["initContainers"][1]["image"] = get_cli_image_pullspec()
    deployment["spec"]["template"]["spec"]["initContainers"][1]["command"] = ["/bin/bash", "-c", load_entrypoint_script()]
    return deployment


def patch_object(object_name, namespace, patch):
    args = [
        shutil.which("oc"),
        "patch",
        object_name,
        "--namespace", namespace,
        "--patch=" + json.dumps(patch),
        "--type=merge"
    ]

    return subprocess.Popen(args)


def use_custom_control_plane_operator(hostedcluster, image):
    patch = {
        "metadata": {
            "annotations": {
                "hypershift.openshift.io/control-plane-operator-image": image,
            }
        }
    }

    return patch_object(
            "hostedcluster/" + hostedcluster["metadata"]["name"],
            hostedcluster["metadata"]["namespace"],
            patch)


def items_to_k8s_list(items):
    return {
        "apiVersion": "v1",
        "items": items,
        "kind": "List",
    }

def setup_oc_build():
    subprocess.run([
        shutil.which("oc"),
        "new-build",
        "--name", "hypershift-operator",
        "--namespace", HYPERSHIFT_NAMESPACE,
        "--binary=true",
    ], env=os.environ).check_returncode()


def apply_manifest(manifest):
    subprocess.run([
        shutil.which("oc"),
        "apply",
        "-f",
        "-"
    ], env=os.environ, input=json.dumps(manifest), text=True).check_returncode()


def add_trigger_to_hypershift_operator():
    operator_trigger = [
        {
            "from": {
            "kind": "ImageStreamTag",
            "name": "hypershift-operator:latest"
            },
            "fieldPath": "spec.template.spec.containers[?(@.name==\"operator\")].image"
        }
    ]

    operator_trigger_patch = {
        "metadata": {
            "annotations": {
                "image.openshift.io/triggers": json.dumps(operator_trigger)
            }
        }
    }

    patch_object("deployment/operator", HYPERSHIFT_NAMESPACE, operator_trigger_patch).wait()


manifests = load_manifests()

setup_oc_build()

apply_manifest({
    "apiVersion": "v1",
    "items": [
        inject_incluster_script(manifests[0]),
        prepare_deployment(manifests[1]),
    ],
    "kind": "List",
})

add_trigger_to_hypershift_operator()
