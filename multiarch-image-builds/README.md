# multiarch image build experiments

These are some very experimental sample configs for performing multiarch in-cluster image builds in OpenShift.
They may or may not work for you, so ¯\_(ツ)_/¯

## Background

Docker has a [built-in
mechanism](https://www.docker.com/blog/multi-arch-build-and-images-the-simple-way/)
for performing multiarch container builds, which is fairly straightforward. I'm
unsure of the mechanism it uses for emulating other architectures, but my guess
is that it uses a similar mechanism to Buildah, albeit with more abstraction
and orchestration around it.

Buildah is the preferred container builder due to a variety of reasons such as
being able to run unprivileged. Buildah supports multiarch container builds via
the `--arch` and `--platform` flags, although it requires a few more steps than
Docker does ([link](https://danmanners.com/posts/2022-01-buildah-multi-arch/)).

How Buildah accomplishes multiarch builds is interesting:
- Buildah uses QEMU to emulate the various CPU types it can target. In particular, it relies upon the `qemu-user-static` package to make this work.
- However, `qemu-user-static` alone is not enough. One also needs to be on a host with [binfmt_misc](https://en.wikipedia.org/wiki/Binfmt_misc) enabled.
- Essentially, the various emulators provided by `qemu-user-static` get registered via the `binfmt_misc` mechanism described above so that when Buildah targets a different architecture, the host kernel can transparently execute the binary in the appropriate emulator.

## How do these YAML files work?

The manifests in this directory do the following:
1. We start a DaemonSet on all worker nodes which runs [tonistiigi/binfmt](https://github.com/tonistiigi/binfmt). This is a small Golang binary whose purpose is to register the various emulators provided by the `qemu-user-static` package with the host. [Source](https://rolandsdev.blog/posts/how-to-install-and-run-qemu-on-k8s-nodes/). This does not install the emulators on the host; it just registers them with `binfmt_misc`.
1. We create our own custom Buildah container, based upon `quay.io/buildah/stable:latest` which includes the `qemu-user-static` package.
1. We start an [Indexed Job](https://kubernetes.io/blog/2021/04/19/introducing-indexed-jobs/) which creates a separate pod for each of our target architectures, using a ConfigMap to map the job index to an architecture. Each separate build pushes to a designed OpenShift ImageStream.
1. Once our indexed job is complete, we start another job that assembles the individual images into a manifest and pushes everything to Quay.io. We're pushing to Quay.io because OpenShift ImageStreams do not support manifestlists.

I verified that the aarch64 container can be pulled and ran on an RPi4.

There are a few caveats to this approach:
1. The binfmt DaemonSet described above must run in a privileged pod.
1. When the binfmt DaemonSet is stopped, it does not automatically clean up after itself. One must either modify the DaemonSet to run `-uninstall` or keep a separate uninstall DaemonSet manifest.
1. Even when the DaemonSet is stopped, the underlying node may still have `binfmt_misc` mounted and enabled.
1. The individual Buildah pods must also be privileged.

Sources for inspiration:
- https://danmanners.com/posts/2022-01-buildah-multi-arch/
- https://www.kernel.org/doc/html/latest/admin-guide/binfmt-misc.html
- https://en.wikipedia.org/wiki/Binfmt_misc
- https://access.redhat.com/solutions/1985633 - requires a Red Hat subscription
- https://rolandsdev.blog/posts/how-to-install-and-run-qemu-on-k8s-nodes/
- https://kubernetes.io/blog/2021/04/19/introducing-indexed-jobs/
