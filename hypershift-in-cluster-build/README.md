# Hypershift In-Cluster Build Configs

## Overview

This was an idea that I had to use the magic of OpenShift Image Builds,
ImageStreams, Triggers, etc. to allow me to push my cloned Hypershift source
repository into my sandbox cluster. The purpose behind this is to speed up my
development loop by taking advantage of the fact that I have an internet
connection with plenty of upload bandwidth and a development cluster with many
powerful CPUs.

Unfortunately, I was unable to actually make this work the way I wanted (see
Limitations). It was still a good exercise in learning more about OpenShift. I've kept these libraries I.

## Details

The idea works thusly:

1. Create a BuildConfig and an ImageStream in the Hypershift operator namespace.
1. Set up an [ImageStream trigger](https://docs.openshift.com/container-platform/4.11/openshift_images/triggering-updates-on-imagestream-changes.html) on the Hypershift operator deployment to update its image pullspec whenever a build is performed.
1. Add another deployment that runs in the Hypershift namespace that also consumes the Hypershift operator image, but effectively no-ops it in an initContainer. Because initContainers are executed sequentially and not in parallel, we wait for that container to initialize first.
1. The aforementioned deployment also includes a Python script that will log into the cluster using the hypershift operator serviceaccount and then update the `hypershift.openshift.io/control-plane-operator-image` annotation on all the hostedclusters so they start using the new ImageStream.

To that end, the `setup-hypershift-env.py` script can be run to configure the development cluster for this to work.

## Limitations

I ran into two limitations:

1. ImageStreams need some [additional configuration](https://docs.openshift.com/container-platform/4.11/openshift_images/managing_images/using-image-pull-secrets.html#images-allow-pods-to-reference-images-across-projects_using-image-pull-secrets) to pull images between namespaces / projects. What's unknown if the operator serviceaccount in the Hypershift namespace has the correct permissions to set that up.
1. The image registry client used within Hypershift to perform the update expects a v2 registry (manifestlisted). Currently, ImageStreams do not support manifestlists and whether they ever will is currently unknown.
